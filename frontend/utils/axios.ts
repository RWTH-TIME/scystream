import axios from "axios"
import getConfig from "next/config"

const config = getConfig()

/*
  This is the global configuration for axios
*/

const api = axios.create({
  baseURL: config.apiUrl,
})

export {
  api
}
