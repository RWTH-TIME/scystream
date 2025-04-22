export enum ProjectStatus {
  RUNNING = "RUNNING",
  IDLE = "IDLE",
  FINISHED = "FINISHED",
  FAILED = "FAILED"
}

export type Project = {
  uuid: string,
  name: string,
  created_at: Date,
  // Undefined will be interpreted as idle
  status: ProjectStatus | undefined,
}
