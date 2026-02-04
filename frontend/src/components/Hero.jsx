// import React, { useState, useEffect, useRef } from "react";
// import video1 from "../assets/video1.mp4";
// import video2 from "../assets/video2.mp4";
// import "./Hero.css";

// const videos = [video1, video2];

// const Hero = () => {
//   const [currentIndex, setCurrentIndex] = useState(0);
//   const refs = useRef([]);

//   useEffect(() => {
//     refs.current[currentIndex]?.play();
//   }, [currentIndex]);

//   const handleEnded = () => {
//     setCurrentIndex((prevIndex) =>
//       prevIndex === videos.length - 1 ? 0 : prevIndex + 1
//     );
//   };

//   return (
//     <div className="hero-container">
//       {videos.map((src, index) => (
//         <video
//           key={index}
//           ref={(el) => (refs.current[index] = el)}
//           className={`hero-video ${index === currentIndex ? "active" : "hidden"}`}
//           autoPlay={index === currentIndex}
//           muted
//           playsInline
//           disablePictureInPicture  // <-- disables PiP icon
//           onEnded={index === currentIndex ? handleEnded : undefined}
//         >
//           <source src={src} type="video/mp4" />
//         </video>

//       ))}
//     </div>
//   );
// };

// export default Hero;


import React from "react";
import hero from "../assets/hero1.jpg";
import "./Hero.css";

const Hero = () => {
  return (
    <div className="hero-container" style={{ width: "100%", height: "auto", overflow: "hidden" }}>
      {/* Using only hero image now - Set to auto height to prevent cropping of text in image */}
      <img
        src={hero}
        alt="HeroBackground"
        className="hero-image"
        style={{ width: "100%", height: "auto", display: "block" }}
      />
    </div>
  );
};

export default Hero;
