// JobOps Toolbar Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Mobile navigation toggle
  const menuToggle = document.querySelector('.menu-toggle');
  const navList = document.querySelector('.nav-list');
  
  if (menuToggle && navList) {
    menuToggle.addEventListener('click', function() {
      navList.classList.toggle('active');
      
      // Toggle hamburger animation
      const spans = menuToggle.querySelectorAll('span');
      if (navList.classList.contains('active')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
      } else {
        spans[0].style.transform = 'none';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'none';
      }
    });
  }

  // Close mobile menu when clicking on nav links
  const navLinks = document.querySelectorAll('.nav-list a');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      if (navList.classList.contains('active')) {
        navList.classList.remove('active');
        
        // Reset hamburger animation
        const spans = menuToggle.querySelectorAll('span');
        spans[0].style.transform = 'none';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'none';
      }
    });
  });

  // Close mobile menu when clicking outside
  document.addEventListener('click', function(e) {
    if (!menuToggle.contains(e.target) && !navList.contains(e.target)) {
      if (navList.classList.contains('active')) {
        navList.classList.remove('active');
        
        // Reset hamburger animation
        const spans = menuToggle.querySelectorAll('span');
        spans[0].style.transform = 'none';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'none';
      }
    }
  });

  // Smooth scrolling for navigation links
  const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');
  smoothScrollLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        const headerOffset = 80; // Account for sticky header
        const elementPosition = targetElement.offsetTop;
        const offsetPosition = elementPosition - headerOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // Copy to clipboard functionality
  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(button => {
    button.addEventListener('click', function() {
      const textToCopy = this.getAttribute('data-clipboard-text');
      
      // Create a temporary textarea element
      const tempTextarea = document.createElement('textarea');
      tempTextarea.value = textToCopy;
      document.body.appendChild(tempTextarea);
      
      // Select and copy the text
      tempTextarea.select();
      tempTextarea.setSelectionRange(0, 99999); // For mobile devices
      
      try {
        document.execCommand('copy');
        
        // Visual feedback
        const originalText = this.textContent;
        this.textContent = 'Copied!';
        this.style.backgroundColor = 'var(--color-success)';
        this.style.color = 'var(--color-btn-primary-text)';
        
        setTimeout(() => {
          this.textContent = originalText;
          this.style.backgroundColor = '';
          this.style.color = '';
        }, 2000);
        
      } catch (err) {
        console.error('Failed to copy text: ', err);
        
        // Fallback: show the text to copy
        alert('Copy this command: ' + textToCopy);
      }
      
      // Remove the temporary textarea
      document.body.removeChild(tempTextarea);
    });
  });

  // Add scroll effect to header
  let lastScrollTop = 0;
  const header = document.querySelector('.header');
  
  window.addEventListener('scroll', function() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    if (scrollTop > lastScrollTop && scrollTop > 100) {
      // Scrolling down
      header.style.transform = 'translateY(-100%)';
    } else {
      // Scrolling up
      header.style.transform = 'translateY(0)';
    }
    
    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop; // For Mobile or negative scrolling
  });

  // Add transition to header for smooth hide/show
  header.style.transition = 'transform 0.3s ease-in-out';

  // Intersection Observer for fade-in animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, observerOptions);

  // Observe all cards and sections for animation
  const animatedElements = document.querySelectorAll('.card, .hero__content');
  animatedElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });

  // Add hover effects to feature cards
  const featureCards = document.querySelectorAll('.feature-card');
  featureCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-5px)';
      this.style.transition = 'transform 0.3s ease';
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });

  // Add click tracking for external links (optional analytics)
  const externalLinks = document.querySelectorAll('a[target="_blank"]');
  externalLinks.forEach(link => {
    link.addEventListener('click', function() {
      const url = this.href;
      console.log('External link clicked:', url);
      // You can add analytics tracking here if needed
    });
  });

  // Add keyboard navigation support
  document.addEventListener('keydown', function(e) {
    // Close mobile menu with Escape key
    if (e.key === 'Escape' && navList.classList.contains('active')) {
      navList.classList.remove('active');
      
      // Reset hamburger animation
      const spans = menuToggle.querySelectorAll('span');
      spans[0].style.transform = 'none';
      spans[1].style.opacity = '1';
      spans[2].style.transform = 'none';
    }
  });

  // Performance optimization: throttle scroll events
  let ticking = false;
  
  function updateScrollEffects() {
    // Any scroll-based effects can be added here
    ticking = false;
  }
  
  function requestTick() {
    if (!ticking) {
      requestAnimationFrame(updateScrollEffects);
      ticking = true;
    }
  }
  
  // Replace the direct scroll event listener with throttled version if needed
  // window.addEventListener('scroll', requestTick);
});