import { useState } from "react";
import {
  Check,
  ClipboardCopy,
  Download,
  FileSpreadsheet,
  Info,
  Table2,
  Users,
} from "lucide-react";
import { downloadFile } from "../../api/client";
import type { GroupType } from "../../api/types";
import { GROUP_LABELS } from "../../lib/labels";
import { NEXT_GROUP_TYPE } from "../../lib/groups";
import { fullName } from "../../lib/format";
import type { ParentValue } from "../people/ParentPicker";
import { Badge, Button, Modal } from "../ui";
import { useToast } from "../ui/Toast";

const COLUMNS = [
  { key: "reg_number", label: "Регистрийн дугаар", required: true, hint: "УБ12345678" },
  { key: "last_name", label: "Овог", required: true, hint: "Бат" },
  { key: "first_name", label: "Нэр", required: true, hint: "Болд" },
  { key: "gender", label: "Хүйс", required: true, hint: "Эрэгтэй" },
  { key: "birth_date", label: "Төрсөн огноо", required: false, hint: "1990-01-01" },
  { key: "phone", label: "Утас", required: false, hint: "99110000" },
  { key: "district", label: "Дүүрэг", required: false, hint: "Хан-Уул" },
  { key: "khoroo", label: "Хороо", required: false, hint: "1-р хороо" },
  { key: "address", label: "Хаяг", required: false, hint: "1-р байр 101" },
  { key: "job", label: "Ажил", required: false, hint: "Инженер" },
  { key: "group_type", label: "Бүлгийн төрөл", required: true, hint: "Мянгат" },
  { key: "username", label: "Хэрэглэгчийн нэр", required: false, hint: "bat.bold" },
  { key: "password", label: "Нууц үг", required: false, hint: "10+ тэмдэгт" },
] as const;

type ColumnKey = (typeof COLUMNS)[number]["key"];
type SampleRow = Record<ColumnKey, string>;

const SAMPLE_PEOPLE = [
  ["Бат", "Болд", "Эрэгтэй", "1990-01-01", "99110001", "Хан-Уул", "1-р хороо", "1-р байр 101", "Инженер"],
  ["Бат", "Сараа", "Эмэгтэй", "1992-02-02", "88110002", "Хан-Уул", "1-р хороо", "2-р байр 202", "Багш"],
  ["Дорж", "Тэмүүлэн", "Эрэгтэй", "1994-03-03", "99110003", "Баянзүрх", "5-р хороо", "3-р байр 303", "Жолооч"],
] as const;

function sampleRows(groupType: GroupType): SampleRow[] {
  return SAMPLE_PEOPLE.map((person, index) => {
    const [last_name, first_name, gender, birth_date, phone, district, khoroo, address, job] = person;
    return {
      reg_number: `УБ9900001${index + 1}`,
      last_name,
      first_name,
      gender,
      birth_date,
      phone,
      district,
      khoroo,
      address,
      job,
      group_type: GROUP_LABELS[groupType],
      username: "",
      password: "",
    };
  });
}

function toTsv(rows: SampleRow[]) {
  return [
    COLUMNS.map((column) => column.label).join("\t"),
    ...rows.map((row) => COLUMNS.map((column) => row[column.key] ?? "").join("\t")),
  ].join("\n");
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
  }
}

export function ImportGuideModal({
  open,
  onClose,
  parent,
}: {
  open: boolean;
  onClose: () => void;
  parent: ParentValue | null;
}) {
  const { toast } = useToast();
  const [copied, setCopied] = useState<"sample" | "headers" | null>(null);
  const childGroupType = parent?.group_type ? NEXT_GROUP_TYPE[parent.group_type] : "TUMT";
  const rows = childGroupType ? sampleRows(childGroupType) : [];
  const parentLabel = parent ? `${fullName(parent)} (${parent.reg_number})` : null;

  async function copy(kind: "sample" | "headers") {
    if (kind === "sample" && rows.length === 0) {
      toast("Гишүүн төрөлтэй хүний доор бүртгэл оруулах боломжгүй.", "error");
      return;
    }
    const text = kind === "sample" ? toTsv(rows) : toTsv([]);
    try {
      await copyText(text);
      setCopied(kind);
      toast(
        kind === "sample"
          ? "Жишээ хүснэгт хуулагдлаа. Excel эсвэл Google Sheets-д paste хийнэ үү."
          : "Баганын нэр хуулагдлаа. Хүснэгтийн эхний мөрөнд paste хийнэ үү.",
        "success",
      );
      window.setTimeout(() => setCopied(null), 2200);
    } catch {
      toast("Хуулахад алдаа гарлаа. Гараар сонгоод хуулна уу.", "error");
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="xl"
      title="Импортын хүснэгт хэрхэн бөглөх вэ?"
      description={
        parentLabel
          ? `${parentLabel}-ийн доор ${childGroupType ? GROUP_LABELS[childGroupType] : "доорх"} бүртгэл нэмэх загвар.`
          : "Харьяалагдах хүн сонгоогүй тул зөвхөн Түмт (үндсэн) бүртгэл нэмэх загвар."
      }
      footer={
        <>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download size={14} />}
            onClick={() =>
              void downloadFile("/imports/template").catch((error: Error) =>
                toast(error.message, "error"),
              )
            }
          >
            CSV загвар татах
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={copied === "headers" ? <Check size={14} /> : <ClipboardCopy size={14} />}
            onClick={() => void copy("headers")}
          >
            Зөвхөн баганын нэр хуулах
          </Button>
          <Button
            size="sm"
            icon={copied === "sample" ? <Check size={14} /> : <ClipboardCopy size={14} />}
            onClick={() => void copy("sample")}
          >
            Жишээтэй хуулах
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        {parentLabel && (
          <div className="flex items-start gap-2.5 rounded-xl border border-acid-500/20 bg-acid-500/[0.07] px-3.5 py-3">
            <Users size={16} className="mt-0.5 shrink-0 text-acid-300" />
            <div>
              <p className="text-xs font-semibold text-fg/80">Сонгосон харьяалал</p>
              <p className="mt-0.5 text-[11px] leading-5 text-fg/50">
                {parentLabel} · бүх мөр энэ хүний шууд доор нэмэгдэнэ.
                {childGroupType && ` Бүлгийн төрөл нь ${GROUP_LABELS[childGroupType]} байна.`}
              </p>
            </div>
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-3">
          <Step
            index={1}
            title={parent ? "Харьяалал сонгосон" : "Харьяалал сонго"}
            body={
              parent
                ? "Файлын бүх мөр доорх сонгосон хүнд автоматаар харьяалагдана."
                : "Зөвхөн Түмт оруулах бол хоосон орхино. Бусад төрөл бол эхлээд хүнээ сонгоно."
            }
          />
          <Step
            index={2}
            title="Мэдээллээ бөглө"
            body="Улаанаар тэмдэглэсэн талбарыг заавал бөглөнө. Баганын нэрийг өөрчлөхгүй."
          />
          <Step
            index={3}
            title="Файлаа оруул"
            body="Хүснэгтийг CSV эсвэл XLSX болгон хадгалаад энэ хуудасны «Файл сонгох» товчоор оруулна."
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="brand">
            <Table2 size={11} className="mr-1" /> 13 багана
          </Badge>
          <Badge tone="info">
            <FileSpreadsheet size={11} className="mr-1" /> CSV / XLSX
          </Badge>
          <span className="text-[11px] text-fg/40">
            * тэмдэгтэй багана заавал бөглөгдөнө · Хүснэгтийг хажуу тийш гүйлгэж бүх баганыг харна уу
          </span>
        </div>

        <div className="overflow-hidden rounded-xl border border-fg/[0.09]">
          <div className="max-h-[320px] overflow-auto">
            {rows.length === 0 ? (
              <p className="px-4 py-10 text-center text-xs text-fg/50">
                Гишүүн төрөлтэй хүний доор бүртгэл нэмэх боломжгүй. Өөр харьяалал сонгоно уу.
              </p>
            ) : (
              <table className="w-full min-w-[980px] border-collapse text-left text-[10px]">
                <thead className="sticky top-0 z-10 bg-night-800/95 backdrop-blur-xl">
                  <tr>
                    <th className="w-8 border-b border-fg/[0.08] px-2 py-2.5 font-mono text-[9px] font-medium text-fg/30">
                      #
                    </th>
                    {COLUMNS.map((column) => (
                      <th
                        key={column.key}
                        className="whitespace-nowrap border-b border-fg/[0.08] px-2.5 py-2.5 font-medium text-fg/70"
                      >
                        {column.label}
                        {column.required && <span className="ml-1 text-red-400">*</span>}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr
                      key={row.reg_number}
                      className="border-b border-fg/[0.04] last:border-0 odd:bg-fg/[0.018]"
                    >
                      <td className="px-2 py-2 font-mono text-[9px] text-fg/25">{index + 1}</td>
                      {COLUMNS.map((column) => (
                        <td
                          key={column.key}
                          className={
                            column.key === "reg_number"
                              ? "whitespace-nowrap px-2.5 py-2 font-mono text-[10px] text-fg/70"
                              : "whitespace-nowrap px-2.5 py-2 text-fg/60"
                          }
                        >
                          {row[column.key] || <span className="text-fg/20">—</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="grid gap-3 text-[11px] leading-5 sm:grid-cols-2">
          <div className="rounded-xl border border-fg/[0.08] bg-fg/[0.03] p-3">
            <p className="mb-1 flex items-center gap-1.5 font-semibold text-fg/75">
              <Info size={13} className="text-acid-300" /> Бөглөх дүрэм
            </p>
            <ul className="space-y-1 text-fg/50">
              <li>• Регистр: 2 кирилл үсэг + 8 цифр (жишээ: УБ99000011).</li>
              <li>• Огноо: 1990-01-01 эсвэл 1990.01.01.</li>
              <li>• Утас: 6–15 цифр, эхэндээ + байж болно.</li>
              <li>• Хүйс: Эрэгтэй, Эмэгтэй, Бусад.</li>
              <li>• Нууц үг: 10+ тэмдэгт, дор хаяж нэг үсэг, нэг тоо.</li>
              <li>• Хэрэглэгчийн нэр, нууц үг хоёулаа хоосон бол аккаунт үүсэхгүй.</li>
              <li>• Хэрэглэгчийн нэр хоосон бол нууц үгтэй мөрөнд `user` + ID хэлбэрийн нэр автоматаар үүснэ.</li>
            </ul>
          </div>
          <div className="rounded-xl border border-fg/[0.08] bg-fg/[0.03] p-3">
            <p className="mb-1 flex items-center gap-1.5 font-semibold text-fg/75">
              <Info size={13} className="text-acid-300" /> Харьяаллын дүрэм
            </p>
            <ul className="space-y-1 text-fg/50">
              <li>• Түмт: харьяалагдах хүн сонгохгүй.</li>
              <li>• Бусад: эхлээд дээд шатны хүнээ сонгоно.</li>
              <li>• Бүлгийн төрөл нь сонгосон хүний дараагийн шат байна.</li>
              <li>• Нэг файлд нэг төрлийн бүртгэл оруулна.</li>
            </ul>
          </div>
        </div>
      </div>
    </Modal>
  );
}

function Step({ index, title, body }: { index: number; title: string; body: string }) {
  return (
    <div className="rounded-xl border border-fg/[0.08] bg-fg/[0.035] p-3">
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-acid-500/15 text-[11px] font-semibold text-acid-300 ring-1 ring-inset ring-acid-500/25">
        {index}
      </span>
      <p className="mt-2 text-xs font-semibold text-fg/85">{title}</p>
      <p className="mt-1 text-[11px] leading-5 text-fg/45">{body}</p>
    </div>
  );
}
