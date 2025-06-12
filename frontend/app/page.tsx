import Image from "next/image"
import Link from "next/link"
import preview from "@/public/preview.png"
import expert from "@/public/expert_mode.png"
import Button, { ButtonSentiment } from "@/components/Button"
import { Box, Stack, Typography } from "@mui/material"
import PageWithHeader from "@/components/layout/PageWithHeader"

export default function Home() {
  return (
    <PageWithHeader breadcrumbs={[{ text: "Home", link: "/" }]}>
      {/* Full width gray background */}
      <div className="w-full bg-gray-100 py-16">
        {/* Centered content container */}
        <div className="max-w-7xl mx-auto px-8 flex items-center gap-x-16">
          <Box flex={1} maxWidth={480}>
            <Typography variant="h3" fontWeight={700} gutterBottom>
              Data Pipelines
            </Typography>
            <Typography variant="h6" fontWeight={400} sx={{ opacity: 0.85 }} paragraph>
              Manage and Build your Data Pipelines
            </Typography>
            <Stack direction="row" spacing={2} mt={4}>
              <Link href="/login" passHref>
                <Button sentiment={ButtonSentiment.POSITIVE}>
                  Log In
                </Button>
              </Link>
              <Link href="/sign-up" passHref>
                <Button sentiment={ButtonSentiment.NEUTRAL}>
                  Register
                </Button>
              </Link>
            </Stack>
          </Box>

          <div className="shadow-lg overflow-hidden rounded-lg inline-block">
            <Image
              src={preview}
              width={750}
              alt="Scystream UI Screenshot"
              className="rounded-lg"
            />
          </div>
        </div>
      </div>
      <div className="w-full bg-gradient-to-r from-indigo-900 via-indigo-800 to-indigo-900 text-white py-20">
        <div className="max-w-7xl mx-auto px-8 flex flex-col md:flex-row items-center gap-x-16">
          <div className="shadow-2xl overflow-hidden rounded-lg inline-block mt-12 md:mt-0">
            <Image
              src={expert}
              width={750}
              alt="Expert Mode Screenshot"
              className="rounded-lg"
            />
          </div>

          <Box flex={1} maxWidth={480}>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Expert Mode
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.85 }} paragraph>
              Take full control with our advanced tools designed for power users.
              Visualize, automate, and optimize your pipelines with precision.
            </Typography>
            <Link href="/expert" passHref>
              <Button sentiment={ButtonSentiment.POSITIVE}>
                Explore Expert Mode
              </Button>
            </Link>
          </Box>
        </div>
      </div>
    </PageWithHeader>
  )
}

