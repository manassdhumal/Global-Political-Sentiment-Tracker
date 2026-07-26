import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { ConfigProvider } from "@/components/config-context";
import { AppShell } from "@/components/app-shell";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Global Political Sentiment Tracker",
  description:
    "Media coverage tone and public/social sentiment toward political figures, " +
    "parties and issues — across countries and over time. Not public opinion.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
      <body>
        <Providers>
          <ConfigProvider>
            <AppShell>{children}</AppShell>
          </ConfigProvider>
        </Providers>
      </body>
    </html>
  );
}
