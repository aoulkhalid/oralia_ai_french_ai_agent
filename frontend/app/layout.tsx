export const metadata = {
  title: "Agent IA - Apprentissage du Français",
  description: "Apprenez le français grâce à un agent IA conversationnel",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
