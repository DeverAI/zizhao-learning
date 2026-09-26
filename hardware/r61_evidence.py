#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一份原始串口日志转成**可入库**的分页取证件。

为什么必须有这只：抓下来的 r61z_*_run.log 里带 SoftAP 明文口令，永远不能进仓库；
而"翻页修好了"这句话要成立，就得有落在仓库里的载体。所以取证动作本身做成脚本：
运行时从 provision_ap.c 现读口令宏的值、逐处替换成 [REDACTED]，再抽判据行、
再现场调用 r61_wrap_sim 复算换行/分页表做对照。手抄数字的口子从这里就堵住。

用法：python r61_evidence.py <原始日志> <输出取证件>
输出件不含任何口令明文（脚本对**输出**也做一次断言：出现明文则不落盘）。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r61_wrap_sim as sim                      # noqa: E402

MAIN = os.path.join(HERE, "zizhao-esp32s3", "main")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# 1.54 版面常数（与 eink_display.c 的 BOARD_EPAPER_1IN54 分支同案）
LAYOUT = (6, 16)          # LAY_MSG_Y, EPD_HEIGHT - LAY_MSG_PAGE_BOT


def provision_msg_bytes():
    """真机配网页那条消息的字节串，全部从源文件现读（不在本脚本里另写一份格式串）。"""
    src = sim.read("provision_ap.c")
    fmt = sim.FMT_RE.search(src)
    pwd = sim.PASS_RE.search(src)
    if not fmt or not pwd:
        raise SystemExit("ABORT: provision_ap.c 里找不到格式串或 PROV_PASS 宏")
    return fmt.group(1) % ("Zizhao-Setup-758D", pwd.group(1)), pwd.group(1)


def predict(text_bytes):
    sim.LAY_MSG_Y, sim.PAGE_BOT = LAYOUT[0], 200 - LAYOUT[1]
    rows, pages = sim.paginate(sim.wrap(text_bytes))
    return dict(scalars=(str(len(text_bytes)), str(sum(r[4] for r in rows)),
                         str(len(rows)), str(pages)),
                map=tuple("%d:%d+%d/%dB" % r[:4] for r in rows))


def dev_line(line):
    s = line[line.index("bytes="):]
    sc = re.search(r"bytes=(\d+) sum_adv=(\d+) lines=(\d+) pages=(\d+)", s)
    mp = re.search(r"map=\[(.*?) ?\]", s)
    if not sc or not mp:
        return None
    return dict(scalars=sc.groups(),
                map=tuple(x for x in mp.group(1).split()),
                req=re.search(r"req_page=(\d+)", s).group(1),
                shown=re.search(r"shown_page=(\d+)", s).group(1))


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    raw, out = sys.argv[1], sys.argv[2]
    if os.path.exists(out):
        raise SystemExit("ABORT: 输出件已存在，不覆盖（%s）" % out)
    text = ANSI.sub("", io.open(raw, encoding="utf-8", errors="replace").read())
    lines = text.splitlines()

    msg, pwd = provision_msg_bytes()
    msg_b = msg.encode("utf-8")
    red = msg_b.decode("utf-8").replace(pwd, "[REDACTED]") if pwd else msg
    selftest = ("PAGE SPLIT CHECK 0123456789 PAGE SPLIT CHECK 0123456789 "
                "PAGE SPLIT CHECK 0123456789 PAGE SPLIT CHECK 0123456789 "
                "PAGE SPLIT CHECK 0123456789 P").encode("utf-8")

    elf16 = [l for l in lines if "ELF file SHA256" in l]
    paging = [l for l in lines if "msg paging" in l]
    browse = [l for l in lines if "browse ->" in l]
    verdict = [l for l in lines if "selftest" in l]

    def group(tb):
        p = predict(tb)
        got = [dev_line(l) for l in paging if ("bytes=%d " % len(tb)) in l]
        got = [g for g in got if g]
        return p, got

    pp, pg = group(msg_b)
    sp, sg = group(selftest)
    out_lines = []
    out_lines.append("R61 分页链路取证（本件由 hardware/r61_evidence.py 生成）")
    out_lines.append("原始日志: %s" % os.path.basename(raw))
    out_lines.append("脱敏: 口令宏的值运行时从 provision_ap.c 现读并逐处替换，本件不含明文")
    out_lines.append("")
    out_lines.append("== 镜像身份链 ==")
    for l in elf16:
        out_lines.append(l.strip())
    out_lines.append("")
    out_lines.append("== 配网页（真机消息，脱敏后） ==")
    out_lines.append("MSG %s" % red)
    for l in paging:
        if ("bytes=%d " % len(msg_b)) in l:
            out_lines.append(l[l.index("bytes="):].strip())
    out_lines.append("PREDICT bytes/sum_adv/lines/pages = %s map=%d 项" % (pp["scalars"], len(pp["map"])))
    out_lines.append("MATCH = %s（%d 条真机行全部命中预测）" %
                     (bool(pg) and all(g["scalars"] == pp["scalars"] and g["map"] == pp["map"] for g in pg), len(pg)))
    out_lines.append("")
    out_lines.append("== 多页自检页（纯 ASCII 诊断文本，无口令） ==")
    for l in paging:
        if ("bytes=%d " % len(selftest)) in l:
            out_lines.append(l[l.index("bytes="):].strip())
    out_lines.append("PREDICT bytes/sum_adv/lines/pages = %s map=%d 项" % (sp["scalars"], len(sp["map"])))
    out_lines.append("MATCH = %s（%d 条真机行全部命中预测）" %
                     (bool(sg) and all(g["scalars"] == sp["scalars"] and g["map"] == sp["map"] for g in sg), len(sg)))
    out_lines.append("req_page 取值 = %s" % sorted({g["req"] for g in sg}))
    out_lines.append("shown_page 取值 = %s" % sorted({g["shown"] for g in sg}))
    out_lines.append("")
    out_lines.append("== 其余 msg paging 行（既不是配网页也不是自检页） ==")
    # 为什么单列这一段：一只消息只要没被上面两组认领，它就只存在于 C:\esp 的原始日志里，
    # 仓库侧就复算不到它 —— "命中 0"和"这条门没跑"、"这行取证脚本没抽到"都是同形输出。
    # 所以这里把**所有**未归类的 paging 行逐条列出，并用下一行给出配平读数。
    known = (len(msg_b), len(selftest))
    rest = [l for l in paging if not any(("bytes=%d " % n) in l for n in known)]
    for l in rest:
        out_lines.append(l[l.index("bytes="):].strip())
    out_lines.append("PAGING_TOTAL=%d 归类=%d+%d 其余=%d 配平=%s" %
                     (len(paging), len(pg), len(sg), len(rest),
                      len(paging) == len(pg) + len(sg) + len(rest)))
    out_lines.append("")
    out_lines.append("== 页面环（buttons_inject 驱动，非实物按键） ==")
    out_lines += [l[l.index("browse ->"):].strip() for l in browse]
    out_lines.append("BROWSE_HITS = %d" % len(browse))
    out_lines.append("")
    out_lines.append("== 自检步与判决 ==")
    out_lines += [l[l.index("zizhao:") - 1:].strip() for l in verdict]
    body = "\n".join(out_lines) + "\n"

    if pwd and pwd in body:
        raise SystemExit("ABORT: 输出件里仍含明文口令，不落盘")
    io.open(out, "w", encoding="utf-8", newline="\n").write(body)
    print("WROTE %s (%d B)" % (out, os.path.getsize(out)))
    print("PLAINTEXT_IN_OUTPUT=0  PROVISION_MATCH=%s  SELFTEST_MATCH=%s  BROWSE=%d" %
          (bool(pg) and all(g["scalars"] == pp["scalars"] and g["map"] == pp["map"] for g in pg),
           bool(sg) and all(g["scalars"] == sp["scalars"] and g["map"] == sp["map"] for g in sg),
           len(browse)))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
