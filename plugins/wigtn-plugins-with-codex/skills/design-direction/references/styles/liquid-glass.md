# Liquid Glass

Use sparingly for depth-rich navigation, overlays, or focal controls on products
that already have meaningful background content. Glass is an elevation material,
not a substitute for hierarchy.

## Direction contract

- First design a clear opaque fallback. Add translucency only where seeing the
  layer beneath helps users understand context or depth.
- Define thin, standard, and thick glass tokens with increasing opacity and
  blur. Use at most two levels on one screen.
- Combine translucent fill, subtle border, restrained inner highlight, and soft
  shadow. Avoid relying on blur alone.
- Maintain text contrast over the worst plausible background. Add a scrim or
  raise opacity for variable media.
- Use glass for navigation bars, compact floating controls, sheets, and modal
  surfaces. Keep long reading areas, tables, and form bodies mostly opaque.
- Keep typography neutral and crisp. Avoid thin weights, text glow, and type
  visible through another layer.
- Prefer a quiet environmental gradient or product imagery over decorative
  blobs created solely to make the blur visible.

## Interaction and performance

- Limit `backdrop-filter` area and the number of simultaneously blurred layers.
  Test scrolling and animation on a mid-range mobile device.
- Use 160–240ms opacity/transform transitions. Refraction or specular movement
  must be subtle, optional, and disabled for reduced motion.
- Provide an opaque fallback for unsupported browsers, high-contrast mode, and
  low-power contexts.
- Keep focus rings outside the glass edge and visibly distinct from highlights.

## Avoid

- Glass on every card, nested glass, unreadable transparent inputs, or multiple
  colored shadows.
- Mouse-tracking light effects on dense tools or touch-first screens.
- Copying platform chrome without matching the product’s interaction model.
- Claiming depth while the stacking, hit targets, or modal focus behavior is
  incorrect.

## Done when

The interface remains complete with blur disabled, text passes contrast over all
background states, only a few surfaces pay the blur cost, and depth clarifies
layering instead of adding decoration.
