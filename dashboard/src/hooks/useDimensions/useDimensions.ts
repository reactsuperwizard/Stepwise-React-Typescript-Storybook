import { useState, useCallback, useLayoutEffect } from 'react';

function useDimensions<Element extends HTMLElement>(): [
  (node: Element) => void,
  DOMRect | null,
  Element | null,
] {
  const [dimensions, setDimensions] = useState<DOMRect | null>(null);
  const [node, setNode] = useState<Element | null>(null);

  const ref = useCallback((newNode) => {
    setNode(newNode);
  }, []);

  useLayoutEffect(() => {
    if (node) {
      const measure = () =>
        window.requestAnimationFrame(() =>
          setDimensions(node.getBoundingClientRect()),
        );
      measure();

      window.addEventListener('resize', measure);

      return () => {
        window.removeEventListener('resize', measure);
      };
    }
    return;
  }, [node]);

  return [ref, dimensions, node];
}

export default useDimensions;
