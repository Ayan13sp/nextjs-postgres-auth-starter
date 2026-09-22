import { Navbar } from "@/components/layout/navbar";

export default function AuthLayout({ children }) {
  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
    </div>
  );
}
