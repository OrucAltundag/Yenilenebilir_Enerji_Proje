import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

import { Providers } from "./providers";

export const metadata = {
  title: "Buraki — Yenilenebilir Enerji Karar Destek",
  description:
    "Türkiye geneli ilçe bazlı GES/RES yatırım skorları, harita ve açıklamalar.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
