"use client";

import { Camera } from "lucide-react";
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { getErrorMessage } from "@/lib/errors";
import { toast } from "@/stores/toasts";

import { updateProfile, uploadAvatar } from "../api";
import { isProfileComplete } from "../profile";
import { useAuthStore } from "../store";
import { AuthCard } from "./AuthCard";

const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"];
const MAX_AVATAR_BYTES = 2 * 1024 * 1024; // matches the backend's MAX_UPLOAD_BYTES default

export function ProfileForm() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);

  const [name, setName] = useState(() =>
    user && isProfileComplete(user) ? user.display_name : "",
  );
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const previewRef = useRef<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(
    () => () => {
      if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    },
    [],
  );

  if (!user) return null;

  function onPickFile(event: ChangeEvent<HTMLInputElement>) {
    const picked = event.target.files?.[0];
    event.target.value = ""; // allow re-picking the same file
    if (!picked) return;
    if (!ACCEPTED_TYPES.includes(picked.type)) {
      setError("Choose a PNG, JPEG, GIF or WebP image.");
      return;
    }
    if (picked.size > MAX_AVATAR_BYTES) {
      setError("That image is too large. The limit is 2 MB.");
      return;
    }
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    const url = URL.createObjectURL(picked);
    previewRef.current = url;
    setPreview(url);
    setFile(picked);
    setError(null);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Please enter your name.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      // Avatar first, name last: saving the name completes the profile, which makes
      // AuthGate redirect, so a failed upload keeps the user here with the error visible.
      if (file) {
        setUser(await uploadAvatar(file));
        setFile(null);
      }
      setUser(await updateProfile({ display_name: trimmed }));
      toast.success(`Welcome, ${trimmed}!`);
    } catch (err) {
      setError(getErrorMessage(err));
      setSubmitting(false);
    }
  }

  return (
    <AuthCard title="Your profile" subtitle="Add your name and, if you like, a profile photo.">
      <form onSubmit={onSubmit} noValidate className="flex flex-col items-center gap-6">
        <button
          type="button"
          onClick={() => fileInput.current?.click()}
          aria-label="Choose profile photo"
          className="focus-visible:outline-brand relative rounded-full focus-visible:outline-2 focus-visible:outline-offset-2"
        >
          <Avatar
            name={name || user.phone_number}
            src={preview ?? user.avatar_url}
            color={user.avatar_color}
            size={96}
          />
          <span className="bg-brand ring-surface absolute right-0 bottom-0 flex size-8 items-center justify-center rounded-full text-white ring-2">
            <Camera size={16} />
          </span>
        </button>
        <input
          ref={fileInput}
          type="file"
          accept={ACCEPTED_TYPES.join(",")}
          className="hidden"
          onChange={onPickFile}
        />

        <Input
          label="Name"
          autoFocus
          maxLength={64}
          autoComplete="name"
          placeholder="Your name"
          value={name}
          onChange={(event) => {
            setName(event.target.value);
            setError(null);
          }}
          error={error}
        />

        <Button type="submit" size="lg" fullWidth loading={submitting}>
          Finish
        </Button>
      </form>
    </AuthCard>
  );
}
