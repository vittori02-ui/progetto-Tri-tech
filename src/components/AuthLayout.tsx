type AuthLayoutProps = {
  children: React.ReactNode;
};

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-black px-6 py-10 lg:justify-end lg:px-16">
      <section className="flex w-full max-w-md items-center justify-center">
        {children}
      </section>
    </main>
  );
}
