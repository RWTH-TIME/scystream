export enum ProjectStatus {
  RUNNING = "RUNNING",
  IDLE = "IDLE",
  FINISHED = "FINISHED",
  FAILED = "FAILED"
}

export enum SupersetImportStatus {
  NONE = "none",
  PENDING = "pending",
  IMPORTING = "importing",
  IMPORTED = "imported",
  FAILED = "failed",
}

export type Project = {
  uuid: string,
  name: string,
  created_at: Date,
  status: ProjectStatus | undefined,
  superset_dashboard_url?: string | null,
  superset_import_status?: SupersetImportStatus | string,
  superset_import_error?: string | null,
}
