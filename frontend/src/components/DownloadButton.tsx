interface Props {
  url: string;
  label?: string;
}

export function DownloadButton({ url, label = 'Download CSV' }: Props) {
  return (
    <a
      href={url}
      download
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded bg-card border border-border text-gray-300 hover:text-white hover:border-gray-500 transition-colors no-underline"
    >
      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      {label}
    </a>
  );
}
