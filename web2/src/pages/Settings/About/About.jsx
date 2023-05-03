import PageHeader from "@/components/PageHeader/PageHeader"
import { useStatusStore } from "@/App"
import "./About.scss"

const About = ({ onClose }) => {
  const info = useStatusStore.getState().status.info

  return (
    <>
      <PageHeader title="About" onClose={onClose} />
      <div className="about-body">
        <a className="link" href="http://www.amplipi.com">Amplipi ™</a>
        <br />
        by <a className="link" href="http://www.micro-nova.com">MicroNova</a> ©{" "}
        {new Date(Date.now()).getFullYear()}
        <br />
        Version: {info.version}
        <br />
        Latest: {info.latest_release}
        <br />
        <div className="about-links">
          Links:
            <a className="link" href="/doc">Browsable API</a>
            <a className="link" href="https://github.com/micro-nova/AmpliPi">Github</a>
            <a className="link" href="https://amplipi.discourse.group/">Community</a>
            <a className="link" href="https://github.com/micro-nova/AmpliPi/blob/main/COPYING">
              License
            </a>
            <a
              href={window.location.href}
              onClick={() => {
                window.location.href =
                  "http://" + window.location.hostname + ":19531/entries"
              }}
            >
              Logs
            </a>
        </div>
      </div>
    </>
  )
}

export default About
