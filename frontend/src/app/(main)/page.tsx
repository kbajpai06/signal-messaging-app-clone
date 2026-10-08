import { SignalLogo } from "@/components/ui/SignalLogo";

export default function HomePage() {
  return (
    <div className="bg-surface flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
      <SignalLogo className="text-brand size-20" />
      <h2 className="text-xl font-semibold">Welcome to Signal</h2>
      <p className="text-fg-muted max-w-xs">
        Select a conversation from the list to start messaging.
      </p>
    </div>
  );
}
