import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import QueryProvider from "@/hooks/useQueryClient"
import { AlertProvider } from "@/hooks/useAlert"
import Alert from "@/components/Alert"
import { PublicEnvScript } from "next-runtime-env"


const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "scystream",
  description: "data science pipeline",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode,
}>) {
  return (
    <html lang="en" data-lt-installed="true">
      <head>
        <PublicEnvScript />
      </head>
      <body className={inter.className}>
        <QueryProvider>
          <AlertProvider>
            {children}
            <Alert />
          </AlertProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
