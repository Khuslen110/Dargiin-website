import { Link } from "react-router-dom";
import { Home } from "lucide-react";
import { Button } from "../components/ui";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <p className="text-6xl font-semibold tracking-tight text-fg/20">404</p>
      <h2 className="mt-3 text-lg font-semibold text-fg">Хуудас олдсонгүй</h2>
      <p className="mt-1 text-sm text-fg/50">Таны хайсан хуудас байхгүй эсвэл зөөгдсөн байна.</p>
      <Link to="/" className="mt-5">
        <Button icon={<Home size={16} />}>Хяналтын самбарт буцах</Button>
      </Link>
    </div>
  );
}
