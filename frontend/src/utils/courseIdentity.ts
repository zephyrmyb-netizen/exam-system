import type { Component } from "vue";
import {
  Atom,
  Binary,
  BookOpen,
  Cpu,
  FlaskConical,
  Landmark,
  Languages,
  Leaf,
  Network,
  Scale,
  Sigma,
  Stethoscope,
  TrendingUp,
} from "@lucide/vue";

type CourseIdentityLike = {
  id?: number | string;
  name?: string | null;
  subject?: string | null;
};

export interface CourseIdentity {
  icon: Component;
  /** Inline chip colors: a soft tint of the identity hue behind the hue itself. */
  style: Record<string, string>;
}

// Curated identity hues — saturated enough to read as icon color on their own tint,
// chosen to stay harmonious with the iOS-style token palette in styles/base.css.
const PALETTE = [
  "#007aff", // blue
  "#7c3aed", // violet
  "#0d9488", // teal
  "#059669", // emerald
  "#d97706", // amber
  "#db2777", // rose
  "#4f46e5", // indigo
  "#0891b2", // cyan
] as const;

// Subject keyword → icon. Matched against "subject + name", first hit wins.
const SUBJECT_ICONS: Array<[RegExp, Component]> = [
  [/数据结构|算法/, Binary],
  [/网络|计算机|软件|编程|代码|信息技术/, Network],
  [/数学|高数|代数|几何|微积分/, Sigma],
  [/英语|英文|语言|语文|日语|韩语|外语/, Languages],
  [/物理/, Atom],
  [/化学/, FlaskConical],
  [/生物|生态/, Leaf],
  [/历史/, Landmark],
  [/政治|法律|法学/, Scale],
  [/经济|金融|会计|管理|营销/, TrendingUp],
  [/医学|护理|临床|药学/, Stethoscope],
  [/电子|电路|硬件|嵌入式|通信/, Cpu],
];

function hashSeed(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return hash;
}

/**
 * Stable per-course visual identity: an icon derived from the subject and a
 * color derived from the course id, so the same course always looks the same
 * in every list while neighbouring courses are easy to tell apart.
 */
export function getCourseIdentity(course: CourseIdentityLike): CourseIdentity {
  const haystack = `${course.subject ?? ""} ${course.name ?? ""}`;
  const icon = SUBJECT_ICONS.find(([pattern]) => pattern.test(haystack))?.[1] ?? BookOpen;
  const seed = String(course.id ?? course.subject ?? course.name ?? "");
  const color = PALETTE[hashSeed(seed) % PALETTE.length];
  return {
    icon,
    style: {
      background: `color-mix(in srgb, ${color} 14%, transparent)`,
      color,
    },
  };
}
