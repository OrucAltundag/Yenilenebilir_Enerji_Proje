import Link from "next/link";

export default function MethodologyPage() {
  return <main className="page-shell"><Link href="/" className="back-link">← Ana sayfa</Link><header className="hero-header"><div><h1>Metodoloji</h1><p className="muted">Skorların, modelin ve açıklanabilirlik katmanının nasıl çalıştığı.</p></div></header><section className="panel prose"><h2>Karar yaklaşımı</h2><p>Deterministik skor motoru birincil karar kaynağıdır. XGBoost bu skoru öğrenen yardımcı model, SHAP ise tahminleri açıklayan katmandır.</p><h2>GES ve RES</h2><p>GES; güneşlenme, arazi, eğim ve teşvik değişkenlerini; RES ise rüzgâr, arazi, eğim ve teşvik değişkenlerini ayrı ağırlıklarla değerlendirir.</p><h2>Sınırlar</h2><p>Sonuçlar yatırım tavsiyesi değildir. Finansal fizibilite, şebeke bağlantısı, mülkiyet, çevresel etki ve saha ölçümleri ayrıca değerlendirilmelidir.</p><h2>Sürümler</h2><p>Veri ve skor metodolojisi sürümü: 2023.1. Her API sonucu kullanılan sürüm bilgisini taşır.</p></section></main>;
}
