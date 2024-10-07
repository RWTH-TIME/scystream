import { z } from "zod"

// This file should include all of our core types

export type Project = {
  uuid: string,
  name: string,
  created_at: Date
}

