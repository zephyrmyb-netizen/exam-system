type CourseLike = {
  id?: number | string;
  name?: string | null;
  question_count?: number | null;
};

export function getCourseDisplayName(course: CourseLike): string {
  const name = course.name?.trim();
  return name || "未命名题库";
}

export function isPracticeReadyCourse(course: CourseLike): boolean {
  return (course.question_count ?? 0) > 0;
}
