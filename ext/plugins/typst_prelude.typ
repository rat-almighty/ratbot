#set page(
  width: 30em,
  height: auto,
)

// Character-level justification makes justified text look just a little nicer
// Of course, if our users `set par(justify: false)`, it does nothing
#set par(justification-limits: (
  tracking: (min: -0.01em, max: 0.02em),
))
