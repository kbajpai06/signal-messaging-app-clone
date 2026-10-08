"use client";

import { LogOut, Settings } from "lucide-react";

import { Avatar } from "@/components/ui/Avatar";
import { Dropdown, type DropdownItem } from "@/components/ui/Dropdown";
import { toast } from "@/stores/toasts";

import { useAuthStore } from "../store";

export function ProfileMenu() {
  const user = useAuthStore((s) => s.user);
  const signOut = useAuthStore((s) => s.signOut);
  if (!user) return null;

  const items: DropdownItem[] = [
    {
      key: "settings",
      label: "Settings",
      icon: <Settings size={16} />,
      onSelect: () => toast.info("Settings are coming soon"),
    },
    {
      key: "logout",
      label: "Log out",
      icon: <LogOut size={16} />,
      destructive: true,
      onSelect: () => void signOut(),
    },
  ];

  return (
    <Dropdown
      items={items}
      align="start"
      header={
        <div className="px-3 py-2">
          <p className="truncate text-sm font-semibold">{user.display_name}</p>
          <p className="text-fg-muted truncate text-xs">{user.phone_number}</p>
        </div>
      }
      trigger={({ open, toggle }) => (
        <button
          type="button"
          onClick={toggle}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label="Account menu"
          className="focus-visible:outline-brand rounded-full focus-visible:outline-2 focus-visible:outline-offset-2"
        >
          <Avatar
            name={user.display_name}
            src={user.avatar_url}
            color={user.avatar_color}
            size={36}
          />
        </button>
      )}
    />
  );
}
