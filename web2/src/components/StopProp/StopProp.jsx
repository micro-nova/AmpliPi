const StopProp = ({ children }) => {
  return <div onClick={(e) => e.stopPropagation()}>{children}</div>
}

export default StopProp
