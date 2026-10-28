export type Role = "ADMIN" | "LEADER" | "MEMBER";
export type GroupType = "TUMT" | "MYANGAT" | "ZUUT" | "ARAVT" | "MEMBER";
export type Gender = "MALE" | "FEMALE" | "OTHER";
export type PersonStatus = "ACTIVE" | "DELETED";
export type ImportStatus = "PREVIEWED" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface Permissions {
  can_edit: boolean;
  can_import: boolean;
  can_export: boolean;
  can_view_sensitive: boolean;
  can_delete: boolean;
  can_manage_users: boolean;
  can_add_child: boolean;
}

export interface CurrentUser {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  is_admin: boolean;
  permissions: Permissions;
  leader_person: LeaderRef | null;
  leader_group_type: GroupType | null;
  next_group_type: GroupType | null;
}

export interface SessionResponse {
  user: CurrentUser;
  csrf_token: string;
}

export interface LeaderRef {
  id: number;
  reg_number: string;
  last_name: string;
  first_name: string;
  group_type: GroupType;
  status: PersonStatus;
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface UserRef {
  id: number;
  username: string;
  full_name: string;
}

export interface PersonRef {
  id: number;
  reg_number: string;
  last_name: string;
  first_name: string;
  status: PersonStatus;
}

export interface PersonSummary {
  id: number;
  reg_number: string;
  last_name: string;
  first_name: string;
  gender: Gender;
  birth_date: string | null;
  age: number | null;
  phone: string | null;
  district: string | null;
  khoroo: string | null;
  group_type: GroupType;
  parent_id: number | null;
  status: PersonStatus;
  full_profile: boolean;
  created_at: string;
  updated_at: string;
}

export interface PersonPermissions {
  can_edit: boolean;
  can_add_child: boolean;
  can_delete: boolean;
  can_restore: boolean;
  can_purge: boolean;
  can_view_sensitive: boolean;
  can_view_full: boolean;
  can_manage_account: boolean;
}

export interface PersonDetail extends PersonSummary {
  address: string | null;
  job: string | null;
  created_by: UserRef | null;
  parent: PersonRef | null;
  path: PersonRef[];
  direct_member_count: number;
  deleted_at: string | null;
  permissions: PersonPermissions;
}

export interface HierarchyNode extends PersonSummary {
  direct_member_count: number;
}

export interface ParentCandidate {
  id: number;
  reg_number: string;
  last_name: string;
  first_name: string;
  group_type: GroupType;
}

export interface PersonAccount {
  id: number;
  username: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface PersonAccountState {
  account: PersonAccount | null;
}

export interface PersonPayload {
  reg_number?: string;
  last_name: string;
  first_name: string;
  gender: Gender;
  birth_date?: string | null;
  phone?: string | null;
  district?: string | null;
  khoroo?: string | null;
  address?: string | null;
  job?: string | null;
  group_type: GroupType;
  parent_id?: number | null;
}

export interface AuditActor {
  id: number;
  username: string;
  full_name: string;
}

export interface AuditItem {
  id: number;
  action: string;
  actor: AuditActor | null;
  entity_type: string | null;
  entity_id: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface GroupCount {
  group_type: GroupType;
  count: number;
}

export interface GenderCount {
  gender: Gender;
  count: number;
}

export interface LabeledCount {
  name: string;
  count: number;
}

export interface AgeBucket {
  label: string;
  min_age: number | null;
  max_age: number | null;
  count: number;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface DashboardStats {
  total_people: number;
  active_people: number;
  deleted_people: number;
  created_today: number;
  created_last_7_days: number;
  group_counts: GroupCount[];
  gender_counts: GenderCount[];
  district_counts: LabeledCount[];
  khoroo_counts: LabeledCount[];
  age_counts: AgeBucket[];
  daily_registrations: DailyCount[];
  recent_people: PersonSummary[];
  recent_actions: AuditItem[];
  pending_imports: number;
  unread_notifications: number;
  scope_label: string;
}

export interface Notification {
  id: number;
  title: string;
  body: string;
  kind: "INFO" | "SUCCESS" | "WARNING";
  read_at: string | null;
  created_at: string;
}

export interface NotificationList {
  items: Notification[];
  unread_count: number;
}

export interface ImportErrorItem {
  row: number;
  message: string;
  field?: string | null;
}

export interface ImportPreview {
  job_id: string;
  filename: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: ImportErrorItem[];
  can_confirm: boolean;
  accounts_planned: number;
}

export interface ImportJob {
  id: string;
  filename: string;
  status: ImportStatus;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  imported_rows: number;
  accounts_created: number;
  errors: ImportErrorItem[];
  created_at: string;
  completed_at: string | null;
}

export interface UserListItem {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  leader_person: LeaderRef | null;
}

export interface UserCreatePayload {
  username: string;
  full_name: string;
  password: string;
  role: Role;
  leader_person_id?: number | null;
}

export interface UserUpdatePayload {
  full_name?: string;
  role?: Role;
  is_active?: boolean;
  leader_person_id?: number | null;
}

export interface ApiErrorBody {
  detail?: string;
  code?: string;
  fields?: Record<string, string>;
}
