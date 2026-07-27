import "./globals.css";

export const metadata = {
  title: "RAGFlow",
  description: "Enterprise AI Knowledge Assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
