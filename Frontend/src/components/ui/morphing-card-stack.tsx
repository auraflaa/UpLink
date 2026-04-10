"use client"

import { useState, type ReactNode } from "react"
import { motion, AnimatePresence, type PanInfo } from "motion/react"
import { cn } from "@/src/lib/utils"

export interface CardData {
  id: string
  title: string
  description: string
  icon?: ReactNode
  color?: string
}

export interface MorphingCardStackProps {
  cards?: CardData[]
  className?: string
  onCardClick?: (card: CardData) => void
}

const SWIPE_THRESHOLD = 50

export function Component({
  cards = [],
  className,
  onCardClick,
}: MorphingCardStackProps) {
  const [activeIndex, setActiveIndex] = useState(0)
  const [isDragging, setIsDragging] = useState(false)

  if (!cards || cards.length === 0) {
    return null
  }

  const handleDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const { offset, velocity } = info
    const swipe = Math.abs(offset.x) * velocity.x

    if (offset.x < -SWIPE_THRESHOLD || swipe < -1000 || offset.x > SWIPE_THRESHOLD || swipe > 1000) {
      setActiveIndex((prev) => (prev + 1) % cards.length)
    }
    setIsDragging(false)
  }

  const getStackOrder = () => {
    const reordered = []
    for (let i = 0; i < cards.length; i++) {
      const index = (activeIndex + i) % cards.length
      reordered.push({ ...cards[index], stackPosition: i })
    }
    return reordered.reverse()
  }

  const displayCards = getStackOrder()

  return (
    <div className={cn("flex flex-col items-center", className)}>
      {/* Stack Container */}
      <div className="relative" style={{ width: 240, height: 220 }}>
        <AnimatePresence mode="popLayout">
          {displayCards.map((card) => {
            const isTopCard = card.stackPosition === 0
            const pos = card.stackPosition

            return (
              <motion.div
                key={card.id}
                layoutId={card.id}
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{
                  opacity: pos > 3 ? 0 : 1,
                  scale: 1,
                  y: 0,
                  x: pos * 8,
                  zIndex: cards.length - pos,
                  rotate: pos * 3,
                }}
                exit={{ opacity: 0, scale: 0.85, x: -200, rotate: -8 }}
                transition={{
                  type: "spring",
                  stiffness: 320,
                  damping: 26,
                }}
                drag={isTopCard ? "x" : false}
                dragConstraints={{ left: 0, right: 0 }}
                dragElastic={0.6}
                onDragStart={() => setIsDragging(true)}
                onDragEnd={handleDragEnd}
                whileDrag={{ scale: 1.04, rotate: -3, cursor: "grabbing" }}
                onClick={() => {
                  if (isDragging) return
                  if (isTopCard) {
                    setActiveIndex((prev) => (prev + 1) % cards.length)
                  }
                  onCardClick?.(card)
                }}
                className={cn(
                  "absolute top-0 left-0 rounded-2xl border border-neutral-200 dark:border-neutral-700/60 bg-white dark:bg-neutral-900 p-5 shadow-lg dark:shadow-xl",
                  "transition-colors",
                  isTopCard && "cursor-grab active:cursor-grabbing border-neutral-300 dark:border-neutral-600/60 hover:border-neutral-400 dark:hover:border-neutral-500/60",
                )}
                style={{
                  width: 240,
                  height: 200,
                  backgroundColor: card.color || undefined,
                }}
              >
                <div className="flex flex-col h-full">
                  {card.icon && (
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 mb-3 border border-neutral-200 dark:border-neutral-700/50">
                      {card.icon}
                    </div>
                  )}
                  <h3 className="font-bold text-neutral-900 dark:text-white text-[15px] leading-tight">{card.title}</h3>
                  <p className="text-[13px] text-neutral-500 dark:text-neutral-400 mt-1.5 leading-relaxed line-clamp-3">
                    {card.description}
                  </p>
                  {isTopCard && (
                    <p className="mt-auto text-[11px] text-neutral-400 dark:text-neutral-600 pt-3">
                      Swipe to navigate
                    </p>
                  )}
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>

      {/* Dot indicators */}
      {cards.length > 1 && (
        <div className="flex justify-center gap-1.5 mt-6">
          {cards.map((_, index) => (
            <button
              key={index}
              onClick={() => setActiveIndex(index)}
              className={cn(
                "h-1.5 rounded-full transition-all duration-300",
                index === activeIndex
                  ? "w-5 bg-neutral-800 dark:bg-white"
                  : "w-1.5 bg-neutral-300 dark:bg-neutral-700 hover:bg-neutral-400 dark:hover:bg-neutral-600",
              )}
              aria-label={`Go to card ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  )
}
