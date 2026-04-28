export function AppHeader({ title }: { title: string }) {
  return (
    <header className="relative flex items-center justify-between px-6 py-4">
      <h1
        className="flex items-center gap-2.5 text-xl font-semibold tracking-tight text-[var(--chocolate-brown)]"
        style={{ fontFamily: "var(--font-display)" }}
      >
        <img src="/hashbrown.svg" alt="Hashbrown" width={22} height={22} className="h-5.5 w-5.5" />
        <img
          src="/copilotkit.svg"
          alt="CopilotKit"
          width={22}
          height={22}
          className="h-5.5 w-5.5"
        />
        <span aria-hidden="true" className="mx-0.5 inline-block h-5 w-px bg-[var(--input)]" />
        {title}
      </h1>
      <div
        className="absolute bottom-0 left-6 right-6 h-px"
        style={{
          background:
            "linear-gradient(90deg, var(--sunshine-yellow) 0%, var(--sky-blue) 50%, transparent 100%)",
          opacity: 0.35,
        }}
      />
    </header>
  );
}
