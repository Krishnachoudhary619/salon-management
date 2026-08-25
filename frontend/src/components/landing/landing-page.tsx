import { About } from "./about";
import { BookingCta } from "./booking-cta";
import { Contact } from "./contact";
import { Gallery } from "./gallery";
import { Hero } from "./hero";
import { LandingFooter } from "./landing-footer";
import { LandingHeader } from "./landing-header";
import { LandingJsonLd } from "./json-ld";
import { Services } from "./services";
import { Team } from "./team";
import { Testimonials } from "./testimonials";
import { WhyChooseUs } from "./why-choose-us";

export function LandingPage() {
  return (
    <div className="landing min-h-screen bg-ink text-ivory">
      <LandingJsonLd />
      <LandingHeader />
      <main>
        <Hero />
        <WhyChooseUs />
        <Services />
        <About />
        <Team />
        <Gallery />
        <Testimonials />
        <BookingCta />
        <Contact />
      </main>
      <LandingFooter />
    </div>
  );
}
