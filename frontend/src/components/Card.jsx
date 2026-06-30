function Card({ title, children }) {
  return (
    <div
      className="
        bg-white
        rounded-2xl
        border-l-4
        border-sky-500
        p-6
        shadow-md
        hover:shadow-xl
        hover:-translate-y-1
        transition-all
        duration-300
      "
    >
      {title && (
        <h3 className="text-xl font-semibold text-slate-800 mb-5">
          {title}
        </h3>
      )}

      {children}
    </div>
  );
}

export default Card;