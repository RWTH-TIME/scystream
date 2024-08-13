import axios from "axios"
import { getConfig } from "./config"

const config = getConfig()

/*
  This is the global configuration for axios
*/

const api = axios.create({
  baseURL: config.apiUrl,
})

api.defaults.headers.common["Content-Type"] = "application/json"

export {
  api
}
