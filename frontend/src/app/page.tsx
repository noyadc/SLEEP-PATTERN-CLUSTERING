import Link from "next/link";
import { Moon, BarChart3, Brain, Shield, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <header className="glass-nav">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Moon className="h-6 w-6 text-indigo-400" />
            <span className="text-lg font-bold gradient-text">SleepAnalytics</span>
          </div>
          <div className="flex gap-3">
            <Button variant="ghost" asChild>
              <Link href="/login">Sign In</Link>
            </Button>
            <Button asChild>
              <Link href="/signup">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="container mx-auto px-4 py-24 text-center">
        <h1 className="text-5xl md:text-6xl font-bold mb-6">
          Understand Your <span className="gradient-text">Sleep Patterns</span>
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
          Upload wearable data, discover your sleep archetype with ML clustering,
          and get personalized recommendations powered by explainable AI.
        </p>
        <div className="flex gap-4 justify-center">
          <Button size="lg" asChild>
            <Link href="/signup">Start Free Analysis</Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/login">Sign In</Link>
          </Button>
        </div>
      </section>

      <section className="container mx-auto px-4 py-16 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { icon: Upload, title: "Multi-Source Upload", desc: "Fitbit, Apple Health, and Garmin exports" },
          { icon: Brain, title: "ML Clustering", desc: "K-Means and hierarchical sleep archetypes" },
          { icon: BarChart3, title: "Lifestyle Analytics", desc: "Correlation, ANOVA, and chi-square testing" },
          { icon: Shield, title: "Explainable AI", desc: "SHAP visualizations and risk alerts" },
        ].map(({ icon: Icon, title, desc }) => (
          <div key={title} className="stat-card text-center">
            <Icon className="h-10 w-10 mx-auto mb-4 text-indigo-400" />
            <h3 className="font-semibold mb-2">{title}</h3>
            <p className="text-sm text-muted-foreground">{desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
