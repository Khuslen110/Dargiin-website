import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeft, Info, LockKeyhole, Save, UserRoundPlus } from "lucide-react";
import { api, ApiError } from "../api/client";
import type { GroupType, PersonDetail, PersonPayload } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import {
  Button,
  Card,
  ErrorState,
  Field,
  Input,
  Select,
  Spinner,
  Textarea,
} from "../components/ui";
import { PageHeader } from "../components/layout/AppShell";
import { useToast } from "../components/ui/Toast";
import { ParentPicker, type ParentValue } from "../components/people/ParentPicker";
import { GENDER_LABELS, GROUP_DESCRIPTIONS, GROUP_LABELS } from "../lib/labels";
import { PARENT_GROUP_TYPE } from "../lib/groups";

const optionalText = z
  .string()
  .trim()
  .max(255, "Хэт урт утга")
  .optional()
  .transform((value) => value || undefined);

const schema = z.object({
  reg_number: z.string().trim().min(1, "Регистрийн дугаар оруулна уу").max(20),
  last_name: z.string().trim().min(1, "Овог оруулна уу").max(80),
  first_name: z.string().trim().min(1, "Нэр оруулна уу").max(80),
  gender: z.enum(["MALE", "FEMALE", "OTHER"]),
  birth_date: z.string().optional(),
  phone: z.string().trim().max(30).optional(),
  district: optionalText,
  khoroo: optionalText,
  address: optionalText,
  job: optionalText,
  group_type: z.enum(["TUMT", "MYANGAT", "ZUUT", "ARAVT", "MEMBER"]),
});

type FormValues = z.infer<typeof schema>;

export default function PersonFormPage() {
  const { personId } = useParams();
  const isEdit = Boolean(personId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { toast } = useToast();
  const [parent, setParent] = useState<ParentValue | null>(null);
  const [parentError, setParentError] = useState("");
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});
  const [createAccount, setCreateAccount] = useState(false);
  const [accountUsername, setAccountUsername] = useState("");
  const [accountPassword, setAccountPassword] = useState("");
  const [accountError, setAccountError] = useState("");

  const detailQuery = useQuery({
    queryKey: ["person", Number(personId)],
    queryFn: () => api.get<PersonDetail>(`/people/${personId}`),
    enabled: isEdit,
  });

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      reg_number: "",
      last_name: "",
      first_name: "",
      gender: "MALE",
      birth_date: "",
      phone: "",
      district: "",
      khoroo: "",
      address: "",
      job: "",
      group_type: "TUMT",
    },
  });

  const groupType = watch("group_type");
  const isLeader = Boolean(user && !user.is_admin);
  const parentLocked = isLeader;
  const groupLocked = isLeader && !isEdit;

  useEffect(() => {
    if (!user || user.is_admin) return;
    const nextType = user.next_group_type;
    if (nextType) setValue("group_type", nextType);
    const leader = user.leader_person;
    if (!isEdit && leader) {
      setParent({
        id: leader.id,
        reg_number: leader.reg_number,
        last_name: leader.last_name,
        first_name: leader.first_name,
        group_type: leader.group_type,
      });
    }
  }, [user, isEdit, setValue]);

  useEffect(() => {
    const person = detailQuery.data;
    if (!person) return;
    reset({
      reg_number: person.reg_number,
      last_name: person.last_name,
      first_name: person.first_name,
      gender: person.gender,
      birth_date: person.birth_date ?? "",
      phone: person.phone ?? "",
      district: person.district ?? "",
      khoroo: person.khoroo ?? "",
      address: person.address ?? "",
      job: person.job ?? "",
      group_type: person.group_type,
    });
    setParent(
      person.parent
        ? {
            id: person.parent.id,
            reg_number: person.parent.reg_number,
            last_name: person.parent.last_name,
            first_name: person.parent.first_name,
          }
        : null,
    );
  }, [detailQuery.data, reset]);

  const mutation = useMutation({
    mutationFn: async ({
      payload,
      account,
    }: {
      payload: PersonPayload;
      account: { username: string; password: string } | null;
    }) => {
      const person = isEdit
        ? await api.patch<PersonDetail>(`/people/${personId}`, payload)
        : await api.post<PersonDetail>("/people", payload);
      let accountError: string | null = null;
      if (account) {
        try {
          await api.post(`/people/${person.id}/account`, {
            username: account.username,
            password: account.password,
          });
        } catch (error) {
          accountError =
            error instanceof ApiError
              ? error.message
              : "Нэвтрэх эрх үүсгэхэд алдаа гарлаа.";
        }
      }
      return { person, accountError };
    },
    onSuccess: async ({ person, accountError }) => {
      toast(
        accountError
          ? `Иргэн бүртгэгдлээ, гэхдээ нэвтрэх эрх үүсгэсэнгүй: ${accountError}`
          : isEdit
            ? "Мэдээлэл амжилттай хадгалагдлаа."
            : createAccount
              ? "Иргэн болон нэвтрэх эрх амжилттай үүслээ."
              : "Иргэн амжилттай бүртгэгдлээ.",
        accountError ? "error" : "success",
      );
      await queryClient.invalidateQueries({ queryKey: ["people"] });
      await queryClient.invalidateQueries({ queryKey: ["person", person.id] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      if (createAccount) await queryClient.invalidateQueries({ queryKey: ["users"] });
      navigate(`/people/${person.id}`);
    },
    onError: (error) => {
      if (error instanceof ApiError) {
        setServerErrors(error.fields);
        toast(error.message, "error");
      } else {
        toast("Хадгалахад алдаа гарлаа.", "error");
      }
    },
  });

  if (isEdit && detailQuery.isLoading) return <Spinner />;
  if (isEdit && (detailQuery.isError || !detailQuery.data)) {
    return <ErrorState message="Бүртгэл олдсонгүй эсвэл хандах эрх танд байхгүй." />;
  }

  const parentRequired = groupType !== "TUMT";
  const parentType = PARENT_GROUP_TYPE[groupType];
  const canSubmit = !groupLocked || Boolean(user?.next_group_type);

  function onGroupChange(next: GroupType) {
    setValue("group_type", next, { shouldValidate: true });
    if (parent && parent.group_type !== PARENT_GROUP_TYPE[next]) setParent(null);
    if (next === "TUMT") setParent(null);
    setParentError("");
  }

  async function onSubmit(values: FormValues) {
    setServerErrors({});
    if (parentRequired && !parent) {
      setParentError("Харьяалагдах бүртгэл заавал сонгоно уу.");
      return;
    }
    setParentError("");
    setAccountError("");
    if (!isEdit && createAccount) {
      if (!accountUsername.trim()) {
        setAccountError("Хэрэглэгчийн нэр оруулна уу.");
        return;
      }
      if (accountPassword.length < 10) {
        setAccountError("Нууц үг 10-аас доошгүй тэмдэгт байна.");
        return;
      }
    }
    const payload: PersonPayload = {
      last_name: values.last_name,
      first_name: values.first_name,
      gender: values.gender,
      birth_date: values.birth_date || null,
      phone: values.phone?.trim() || null,
      district: values.district || null,
      khoroo: values.khoroo || null,
      address: values.address || null,
      job: values.job || null,
      group_type: groupLocked && user?.next_group_type ? user.next_group_type : values.group_type,
      parent_id: values.group_type === "TUMT" ? null : (parent?.id ?? null),
    };
    if (!isEdit) payload.reg_number = values.reg_number;
    mutation.mutate({
      payload,
      account:
        !isEdit && createAccount
          ? {
              username: accountUsername.trim(),
              password: accountPassword,
            }
          : null,
    });
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        eyebrow={isEdit ? "Бүртгэл засах" : "Шинэ бүртгэл"}
        title={isEdit ? "Иргэний мэдээлэл засах" : "Шинэ иргэн бүртгэх"}
        description="Регистрийн дугаар, хувийн мэдээлэл болон харьяаллыг зөв бөглөнө үү."
        actions={
          <Button variant="ghost" icon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
            Буцах
          </Button>
        }
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
        <Card className="p-5 sm:p-6">
          <div className="mb-5 flex items-center gap-2">
            <UserRoundPlus size={17} className="text-acid-300" />
            <h3 className="text-sm font-semibold text-fg">Үндсэн мэдээлэл</h3>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label="Регистрийн дугаар"
              htmlFor="reg_number"
              required
              error={errors.reg_number?.message ?? serverErrors.reg_number}
              hint={isEdit ? "Регистрийн дугаарыг өөрчлөх боломжгүй." : "Жишээ: УБ12345678"}
            >
              <Input
                id="reg_number"
                {...register("reg_number")}
                disabled={isEdit}
                placeholder="УБ12345678"
                className="font-mono uppercase"
              />
            </Field>
            <Field
              label="Бүлгийн төрөл"
              htmlFor="group_type"
              required
              error={errors.group_type?.message ?? serverErrors.group_type}
              hint={groupLocked ? "Таны бүртгэх төрөл автоматаар тодорхойлогдоно." : undefined}
            >
              <Select
                id="group_type"
                {...register("group_type")}
                onChange={(event) => onGroupChange(event.target.value as GroupType)}
                disabled={groupLocked || isEdit && isLeader}
              >
                {Object.entries(GROUP_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label} — {GROUP_DESCRIPTIONS[value as GroupType]}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Овог" htmlFor="last_name" required error={errors.last_name?.message ?? serverErrors.last_name}>
              <Input id="last_name" {...register("last_name")} placeholder="Овог" autoComplete="family-name" />
            </Field>
            <Field label="Нэр" htmlFor="first_name" required error={errors.first_name?.message ?? serverErrors.first_name}>
              <Input id="first_name" {...register("first_name")} placeholder="Нэр" autoComplete="given-name" />
            </Field>
            <Field label="Хүйс" htmlFor="gender" required error={errors.gender?.message}>
              <Select id="gender" {...register("gender")}>
                {Object.entries(GENDER_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </Select>
            </Field>
            <Field label="Төрсөн огноо" htmlFor="birth_date" error={errors.birth_date?.message}>
              <Input id="birth_date" type="date" {...register("birth_date")} max={new Date().toISOString().slice(0, 10)} />
            </Field>
          </div>
        </Card>

        <Card className="p-5 sm:p-6">
          <h3 className="mb-5 text-sm font-semibold text-fg">Холбоо барих, байршил</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Утас" htmlFor="phone" error={errors.phone?.message ?? serverErrors.phone} hint="8 оронтой дугаар">
              <Input id="phone" {...register("phone")} placeholder="99112233" inputMode="tel" autoComplete="tel" />
            </Field>
            <Field label="Ажил" htmlFor="job" error={errors.job?.message}>
              <Input id="job" {...register("job")} placeholder="Ажил, албан тушаал" />
            </Field>
            <Field label="Дүүрэг" htmlFor="district" error={errors.district?.message}>
              <Input id="district" {...register("district")} placeholder="Хан-Уул" />
            </Field>
            <Field label="Хороо" htmlFor="khoroo" error={errors.khoroo?.message}>
              <Input id="khoroo" {...register("khoroo")} placeholder="1-р хороо" />
            </Field>
            <Field label="Хаяг" htmlFor="address" className="sm:col-span-2" error={errors.address?.message}>
              <Textarea id="address" {...register("address")} placeholder="Дэлгэрэнгүй хаяг" rows={2} />
            </Field>
          </div>
        </Card>

        <Card className="p-5 sm:p-6">
          <h3 className="mb-1 text-sm font-semibold text-fg">Харьяалал</h3>
          <p className="mb-4 flex items-start gap-2 text-xs text-fg/50">
            {parentLocked || (isEdit && isLeader) ? (
              <>
                <LockKeyhole size={14} className="mt-0.5 shrink-0" />
                {isEdit
                  ? "Харьяалал болон бүлгийн төрлийг зөвхөн администратор өөрчилнө."
                  : `Та зөвхөн өөрийн шууд доорх ${GROUP_LABELS[user?.next_group_type ?? "MEMBER"]} бүртгэл нэмэх боломжтой.`}
              </>
            ) : groupType === "TUMT" ? (
              <>
                <Info size={14} className="mt-0.5 shrink-0" />
                Түмт нь шатлалын үндэс тул эцэг бүртгэлгүй байна.
              </>
            ) : (
              <>
                <Info size={14} className="mt-0.5 shrink-0" />
                {GROUP_LABELS[groupType]} бүртгэлийн эцэг нь зөвхөн {parentType ? GROUP_LABELS[parentType] : "дээд шат"} төрөлтэй байна.
              </>
            )}
          </p>
          <Field
            label="Харьяалагдах бүртгэл"
            required={parentRequired}
            error={parentError}
            hint={parentType && !parentLocked ? `Зөвхөн ${GROUP_LABELS[parentType]} төрлийн бүртгэл харагдана.` : undefined}
          >
            <ParentPicker
              value={parent}
              onChange={(value) => {
                setParent(value);
                setParentError("");
              }}
              excludePersonId={isEdit ? Number(personId) : undefined}
              childGroupType={groupType}
              disabled={parentLocked || (isEdit && isLeader) || groupType === "TUMT"}
            />
          </Field>
        </Card>

        {!isEdit && user?.permissions.can_add_child && (
          <Card className="p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <input
                id="create_account"
                type="checkbox"
                checked={createAccount}
                onChange={(event) => {
                  setCreateAccount(event.target.checked);
                  setAccountError("");
                }}
                className="mt-1 h-4 w-4 rounded border-fg/[0.16] text-acid-400 focus:ring-acid-400"
              />
              <div>
                <label htmlFor="create_account" className="text-sm font-semibold text-fg">
                  Нэвтрэх эрх зэрэг үүсгэх
                </label>
                <p className="mt-1 text-xs leading-5 text-fg/50">
                  Бүртгэсэн хүн системд нэвтрэх шаардлагатай бол энэ хэсгийг бөглөнө.
                  {groupType === "MEMBER"
                    ? " Гишүүнд нэг аравтын гишүүдийг харах эрх оноогдоно."
                    : " Удирдагчид өөрийн модны бүртгэлийг удирдах эрх оноогдоно."}
                  {!user?.is_admin && " Та зөвхөн өөрийн шууд доорх хүнд нэвтрэх эрх үүсгэх боломжтой."}
                </p>
              </div>
            </div>
            {createAccount && (
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <Field
                  label="Хэрэглэгчийн нэр"
                  htmlFor="account_username"
                  required
                  error={accountError && !accountUsername.trim() ? accountError : undefined}
                  hint="Жишээ: bat.erdene"
                >
                  <Input
                    id="account_username"
                    value={accountUsername}
                    onChange={(event) => {
                      setAccountUsername(event.target.value);
                      setAccountError("");
                    }}
                    autoComplete="off"
                  />
                </Field>
                <Field
                  label="Нэвтрэх нууц үг"
                  htmlFor="account_password"
                  required
                  error={accountError && accountPassword.length < 10 ? accountError : undefined}
                  hint="10-аас доошгүй тэмдэгт."
                >
                  <Input
                    id="account_password"
                    type="password"
                    value={accountPassword}
                    onChange={(event) => {
                      setAccountPassword(event.target.value);
                      setAccountError("");
                    }}
                    autoComplete="new-password"
                  />
                </Field>
                <div className="rounded-lg border border-fg/[0.08] bg-fg/[0.03] px-3 py-2 text-xs text-fg/55 sm:col-span-2">
                  Оноох эрх:{" "}
                  <span className="font-medium text-fg/80">
                    {groupType === "MEMBER" ? "Гишүүн" : "Удирдагч"}
                  </span>{" "}
                  · харьяалал автоматаар энэ бүртгэл болно.
                </div>
                {accountError && accountUsername.trim() && accountPassword.length >= 10 && (
                  <p className="text-xs text-rose-400 sm:col-span-2">{accountError}</p>
                )}
              </div>
            )}
          </Card>
        )}

        <div className="flex flex-wrap items-center justify-end gap-2">
          <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
            Болих
          </Button>
          <Button
            type="submit"
            loading={isSubmitting || mutation.isPending}
            disabled={!canSubmit}
            icon={<Save size={16} />}
          >
            {isEdit ? "Өөрчлөлт хадгалах" : "Бүртгэл үүсгэх"}
          </Button>
        </div>
      </form>
    </div>
  );
}
