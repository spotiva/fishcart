"use client";

import { ChangeEvent, useEffect, useId, useRef, useState } from "react";

type ImageUploadPreviewProps = {
  name: string;
  label: string;
  alt: string;
  currentImage?: string | null;
  required?: boolean;
};

function normalizeImageUrl(value: string) {
  try {
    const url = new URL(value, "http://machli.local");
    return url.pathname.startsWith("/media/") ? `${url.pathname}${url.search}` : value;
  } catch {
    return value;
  }
}

export function ImageUploadPreview({
  name,
  label,
  alt,
  currentImage,
  required = false,
}: ImageUploadPreviewProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const previewUrlRef = useRef("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedPreview, setSelectedPreview] = useState("");

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    };
  }, []);

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0] ?? null;
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = file ? URL.createObjectURL(file) : "";
    setSelectedFile(file);
    setSelectedPreview(previewUrlRef.current);
  }

  function clearSelection() {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = "";
    setSelectedFile(null);
    setSelectedPreview("");
    if (inputRef.current) inputRef.current.value = "";
  }

  const imageSrc = selectedPreview || (currentImage ? normalizeImageUrl(currentImage) : "");

  return (
    <div className="image-upload-field span-two">
      <label className="image-upload-label" htmlFor={inputId}>
        {label}
        <input
          ref={inputRef}
          id={inputId}
          name={name}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          required={required}
          onChange={handleChange}
        />
      </label>

      {imageSrc ? (
        <div className="image-preview">
          <img src={imageSrc} alt={alt} />
          <div className="image-preview-copy">
            <strong>{selectedFile ? "Selected image preview" : "Current image"}</strong>
            <small>{selectedFile?.name ?? "Choose a file above to replace it"}</small>
          </div>
          {selectedFile && (
            <button type="button" className="secondary-button" onClick={clearSelection}>
              Clear selection
            </button>
          )}
        </div>
      ) : (
        <div className="image-preview-empty" aria-live="polite">
          <span aria-hidden="true">▧</span>
          <small>Image preview will appear here after you choose a file.</small>
        </div>
      )}
    </div>
  );
}
