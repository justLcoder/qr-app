export const languages = [
  { code: "en", label: "English" },
  { code: "uz", label: "O‘zbekcha" },
  { code: "ru", label: "Русский" },
] as const;

export type Language = (typeof languages)[number]["code"];

export const translations: Record<Language, Record<string, string>> = {
  en: {
    tagline: "URL QR codes that stay useful.", signIn: "Sign in", dashboard: "Dashboard", signOut: "Sign out",
    heroEyebrow: "SIMPLE. EDITABLE. SCANNABLE.", heroTitle: "Make every scan count.", heroDescription: "Create beautiful QR codes for any link. Choose static for one-off sharing, or dynamic to edit the destination and track scans later.",
    static: "Static QR", dynamic: "Dynamic QR", editable: "editable", destination: "Destination URL", label: "Label", optional: "optional", ink: "Ink", paper: "Paper", generate: "Generate QR code", signInRequired: "Create an account to make a dynamic QR code.",
    preview: "LIVE PREVIEW", previewPlaceholder: "Your QR code will appear here", downloadPng: "Download PNG", downloadSvg: "Download SVG", staticCreated: "Static QR code created. Download it below.", dynamicCreated: "Dynamic QR code created — its destination can be changed anytime.",
    workspaceEyebrow: "YOUR WORKSPACE", savedCodes: "Saved QR codes", noCodes: "No saved QR codes yet. Create a dynamic code above to see it here.", scans: "scans", editLink: "Edit link", delete: "Delete", untitled: "Untitled QR code",
    authEyebrow: "QR STUDIO ACCOUNT", welcomeBack: "Welcome back", createAccount: "Create your account", authDescription: "Save dynamic QR codes, change their destination, and monitor every scan.", email: "Email address", password: "Password", login: "Sign in", register: "Create account", google: "Continue with Google", googleUnavailable: "Google sign-in is not configured yet. Use email and password for now.", or: "or continue with email", haveAccount: "Already have an account? Sign in", needAccount: "New to QR Studio? Create an account", backToGenerator: "Back to generator", footer: "Build links that last.",
  },
  uz: {
    tagline: "Foydali bo‘lib qoladigan URL QR-kodlar.", signIn: "Kirish", dashboard: "Boshqaruv", signOut: "Chiqish",
    heroEyebrow: "ODDIY. TAHRIRLANADI. SKANERLANADI.", heroTitle: "Har bir skan muhim.", heroDescription: "Istalgan havola uchun chiroyli QR-kod yarating. Bir martalik ulashish uchun statik, manzilni keyinroq o‘zgartirish va skanlarni kuzatish uchun dinamik kodni tanlang.",
    static: "Statik QR", dynamic: "Dinamik QR", editable: "tahrirlanadi", destination: "Manzil URL'i", label: "Nomi", optional: "ixtiyoriy", ink: "Rang", paper: "Fon", generate: "QR-kod yaratish", signInRequired: "Dinamik QR-kod yaratish uchun hisob oching.",
    preview: "JONLI KO‘RINISH", previewPlaceholder: "QR-kodingiz shu yerda paydo bo‘ladi", downloadPng: "PNG yuklab olish", downloadSvg: "SVG yuklab olish", staticCreated: "Statik QR-kod yaratildi. Quyidan yuklab oling.", dynamicCreated: "Dinamik QR-kod yaratildi — uning manzilini istalgan payt o‘zgartirishingiz mumkin.",
    workspaceEyebrow: "ISH MAYDONINGIZ", savedCodes: "Saqlangan QR-kodlar", noCodes: "Hali saqlangan QR-kod yo‘q. Uni yuqorida yarating.", scans: "skan", editLink: "Havolani tahrirlash", delete: "O‘chirish", untitled: "Nomsiz QR-kod",
    authEyebrow: "QR STUDIO HISOBI", welcomeBack: "Xush kelibsiz", createAccount: "Hisob yarating", authDescription: "Dinamik QR-kodlarni saqlang, manzilini o‘zgartiring va har bir skanni kuzating.", email: "Email manzili", password: "Parol", login: "Kirish", register: "Hisob yaratish", google: "Google orqali davom etish", googleUnavailable: "Google orqali kirish hali sozlanmagan. Hozircha email va paroldan foydalaning.", or: "yoki email orqali", haveAccount: "Hisobingiz bormi? Kiring", needAccount: "QR Studio'da yangimisiz? Hisob yarating", backToGenerator: "Generatorga qaytish", footer: "Uzoq xizmat qiladigan havolalar yarating.",
  },
  ru: {
    tagline: "URL QR-коды, которые остаются полезными.", signIn: "Войти", dashboard: "Панель", signOut: "Выйти",
    heroEyebrow: "ПРОСТО. ИЗМЕНЯЕМО. СКАНИРУЕМО.", heroTitle: "Пусть каждое сканирование имеет значение.", heroDescription: "Создавайте красивые QR-коды для любой ссылки. Выберите статический для разовой публикации или динамический, чтобы позже изменить адрес и отслеживать сканирования.",
    static: "Статический QR", dynamic: "Динамический QR", editable: "изменяемый", destination: "URL назначения", label: "Название", optional: "необязательно", ink: "Цвет", paper: "Фон", generate: "Создать QR-код", signInRequired: "Создайте аккаунт, чтобы сделать динамический QR-код.",
    preview: "ПРЕДПРОСМОТР", previewPlaceholder: "Ваш QR-код появится здесь", downloadPng: "Скачать PNG", downloadSvg: "Скачать SVG", staticCreated: "Статический QR-код создан. Скачайте его ниже.", dynamicCreated: "Динамический QR-код создан — его адрес можно изменить в любое время.",
    workspaceEyebrow: "ВАШЕ ПРОСТРАНСТВО", savedCodes: "Сохранённые QR-коды", noCodes: "Сохранённых QR-кодов пока нет. Создайте динамический код выше.", scans: "сканирований", editLink: "Изменить ссылку", delete: "Удалить", untitled: "QR-код без названия",
    authEyebrow: "АККАУНТ QR STUDIO", welcomeBack: "С возвращением", createAccount: "Создайте аккаунт", authDescription: "Сохраняйте динамические QR-коды, меняйте их адрес и отслеживайте каждое сканирование.", email: "Электронная почта", password: "Пароль", login: "Войти", register: "Создать аккаунт", google: "Продолжить с Google", googleUnavailable: "Вход через Google ещё не настроен. Пока используйте email и пароль.", or: "или через email", haveAccount: "Уже есть аккаунт? Войдите", needAccount: "Впервые в QR Studio? Создайте аккаунт", backToGenerator: "Вернуться к генератору", footer: "Создавайте ссылки, которые остаются полезными.",
  },
};
