import type { AxiosError } from "axios"
import { AlertType, type setAlertType } from "@/hooks/useAlert"

/*
* Use this function to display the default Axios Errors
*/
export default function displayStandardAxiosErrors(error: AxiosError, setAlert: setAlertType) {
  if (error.response) {
    const statusCode = error.response.status
    if (statusCode === 422) {
      setAlert("Validation error: check your inputs.", AlertType.ERROR)
    } else if (statusCode === 401) {
      setAlert("Unauthorized: check your password.", AlertType.ERROR)
    } else if (statusCode === 404) {
      setAlert("User not found.", AlertType.ERROR)
    } else {
      setAlert("Something went wrong.", AlertType.ERROR)
    }
  } else {
    console.log("propagateError called with invalid error type.")
  }
}
