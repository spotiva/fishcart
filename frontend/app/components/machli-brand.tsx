import Image from "next/image";

type MachliBrandProps = {
  className?: string;
  priority?: boolean;
};

export function MachliBrand({
  className = "machli-wordmark",
  priority = false,
}: MachliBrandProps) {
  return (
    <Image
      src="/images/machli-logo.jpeg"
      alt="machli"
      width={1180}
      height={1180}
      className={className}
      priority={priority}
    />
  );
}
