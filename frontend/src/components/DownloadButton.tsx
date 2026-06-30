interface Props {
  url: string;
  label?: string;
}

export function DownloadButton({ url, label = 'Download CSV' }: Props) {
  return (
    <a href={url} download style={{ textDecoration: 'none' }}>
      <button>{label}</button>
    </a>
  );
}
