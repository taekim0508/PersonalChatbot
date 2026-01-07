import { useRef, useEffect, useCallback, useState } from 'react';

export function useAutoScroll<T extends HTMLElement>() {
  const containerRef = useRef<T>(null);
  const [userScrolled, setUserScrolled] = useState(false);
  const lastScrollTop = useRef(0);

  const scrollToBottom = useCallback(() => {
    if (containerRef.current && !userScrolled) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [userScrolled]);

  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;

    // User scrolled up
    if (scrollTop < lastScrollTop.current && !isAtBottom) {
      setUserScrolled(true);
    }

    // User scrolled back to bottom
    if (isAtBottom) {
      setUserScrolled(false);
    }

    lastScrollTop.current = scrollTop;
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [handleScroll]);

  const forceScrollToBottom = useCallback(() => {
    setUserScrolled(false);
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, []);

  return {
    containerRef,
    scrollToBottom,
    forceScrollToBottom,
    userScrolled,
  };
}
