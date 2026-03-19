"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Grid, Environment } from "@react-three/drei";
import { useWorldModelStore } from "@/stores/world-model-store";
import type { Mesh } from "three";

function PhysicsBody({ position, size, type, color }: {
  position: [number, number, number];
  size: [number, number, number];
  type: string;
  color: string;
}) {
  const meshRef = useRef<Mesh>(null);
  const { status } = useWorldModelStore();

  useFrame((_, delta) => {
    if (meshRef.current && status === "running") {
      meshRef.current.rotation.y += delta * 0.2;
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      {type === "sphere" ? (
        <sphereGeometry args={[size[0], 32, 32]} />
      ) : type === "cylinder" ? (
        <cylinderGeometry args={[size[0], size[0], size[1], 32]} />
      ) : (
        <boxGeometry args={size} />
      )}
      <meshStandardMaterial color={color} metalness={0.3} roughness={0.7} />
    </mesh>
  );
}

function SimulationScene() {
  const { currentModel: _currentModel, liveEvents, currentStep: _currentStep } = useWorldModelStore();

  // Get latest state from events for positioning
  const latestEvent = liveEvents[liveEvents.length - 1];
  const bodies = (latestEvent?.observation as { bodies?: { name: string; pos: [number, number, number]; size: [number, number, number]; type: string }[] })?.bodies || [];

  // Default scene if no live data
  const defaultBodies = [
    { name: "base", pos: [0, 0.1, 0] as [number, number, number], size: [2, 0.2, 2] as [number, number, number], type: "box" },
    { name: "arm1", pos: [0, 0.7, 0] as [number, number, number], size: [0.1, 1, 0.1] as [number, number, number], type: "cylinder" },
    { name: "arm2", pos: [0, 1.5, 0.3] as [number, number, number], size: [0.08, 0.8, 0.08] as [number, number, number], type: "cylinder" },
    { name: "gripper", pos: [0, 2, 0.5] as [number, number, number], size: [0.15, 0.15, 0.15] as [number, number, number], type: "sphere" },
  ];

  const displayBodies = bodies.length > 0 ? bodies : defaultBodies;
  const colors = ["#6366f1", "#3b82f6", "#06b6d4", "#10b981", "#f59e0b"];

  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} castShadow />
      <Grid infiniteGrid fadeDistance={20} cellColor="#333" sectionColor="#555" />

      {displayBodies.map((body, i) => (
        <PhysicsBody
          key={body.name}
          position={body.pos}
          size={body.size}
          type={body.type}
          color={colors[i % colors.length]}
        />
      ))}

      <OrbitControls makeDefault />
      <Environment preset="city" />
    </>
  );
}

export function SandboxViewer() {
  return (
    <div className="h-[500px] w-full rounded-lg border border-zinc-800 bg-zinc-950 overflow-hidden">
      <Canvas
        camera={{ position: [3, 3, 3], fov: 50 }}
        shadows
      >
        <SimulationScene />
      </Canvas>
    </div>
  );
}
