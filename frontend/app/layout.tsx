import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import QueryProvider from "@/hooks/useQueryClient"
import { AlertProvider } from "@/hooks/useAlert"
import Alert from "@/components/Alert"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "scystream",
  description: "data science pipeline",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AlertProvider>
          <QueryProvider>
            {children}
            <Alert />
          </QueryProvider>
        </AlertProvider>
      </body>
    </html>
  )
}
