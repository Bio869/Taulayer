import { Github, Twitter, Linkedin, Mail } from "lucide-react";

export const Footer = () => {
  const footerLinks = {
    Product: ["Features", "Pricing", "Documentation", "API Reference"],
    Company: ["About", "Blog", "Careers", "Contact"],
    Resources: ["Help Center", "Community", "Status", "Privacy Policy"],
  };

  return (
    <footer className="bg-background border-t border-border">
      <div className="container px-4 mx-auto py-12">
        <div className="grid md:grid-cols-5 gap-8">
          {/* Logo and description */}
          <div className="md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">U+03C4</span>
              </div>
              <span className="font-bold text-foreground text-xl">Layer</span>
            </div>
            <p className="text-muted-foreground text-sm max-w-md mb-6">
              Intelligent API layer that gives SaaS companies complete visibility and control over LLM-triggered backend operations.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors duration-200">
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors duration-200">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors duration-200">
                <Linkedin className="w-5 h-5" />
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors duration-200">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Footer links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="font-semibold text-foreground mb-4">{category}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-muted-foreground hover:text-foreground transition-colors duration-200 text-sm"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-border mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-muted-foreground text-sm">
            © 2024 OptimizeAI. All rights reserved.
          </p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors duration-200 text-sm">
              Terms of Service
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors duration-200 text-sm">
              Privacy Policy
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};