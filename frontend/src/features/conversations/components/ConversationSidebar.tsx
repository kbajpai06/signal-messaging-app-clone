"use client";

import { MessageSquareText, Search, SquarePen } from "lucide-react";

import { IconButton } from "@/components/ui/IconButton";
import { Input } from "@/components/ui/Input";
import { ProfileMenu } from "@/features/auth";
import { toast } from "@/stores/toasts";

export function ConversationSidebar() {
  return (
    <>
      <header className="flex h-[var(--size-header)] shrink-0 items-center gap-2 px-3">
        <ProfileMenu />
        <h1 className="flex-1 text-base font-semibold">Chats</h1>
        <IconButton label="New message" onClick={() => toast.info("Coming soon")}>
          <SquarePen size={20} />
        </IconButton>
      </header>

      <div className="px-3 pb-2">
        <Input
          filled
          inputSize="sm"
          disabled
          aria-label="Search"
          placeholder="Search"
          leftIcon={<Search size={16} />}
        />
      </div>

      <div className="text-fg-muted flex flex-1 flex-col items-center justify-center gap-2 px-6 text-center">
        <MessageSquareText size={32} />
        <p>No conversations yet</p>
      </div>
    </>
  );
}
