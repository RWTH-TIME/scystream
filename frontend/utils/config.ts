import { z } from "zod"

/*
  We are using zod for schema validation.

  All environment variables, used on the client-side have to be prefixed with
  "NEXT_PUBLIC"

  If environment variables are not set at compile time, build will fail.

  To define custom ENV variables, define them in a .env.local file.
*/

const schema = z.object({
  NODE_ENV: z.literal("production").or(z.literal("development")).default("production"),
  NEXT_PUBLIC_API_URL: z.string().url().default("http://core:4000")
}).transform(obj => ({
  env: obj.NODE_ENV,
  apiUrl: obj.NEXT_PUBLIC_API_URL,
}))

function getConfig() {
  const conf = schema.safeParse({
    NODE_ENV: process.env.NODE_ENV,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  })

  if (!conf.success) {
    throw new Error(`Invalid environment variables:${conf.error}`)
  } else {
    return Object.assign(conf.data)
  }
}

export {
  getConfig
}
