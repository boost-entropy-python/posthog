import { LemonTag } from '@posthog/lemon-ui'
import { useActions, useValues } from 'kea'
import { LemonButton, LemonButtonProps } from 'lib/lemon-ui/LemonButton'
import { Tooltip } from 'lib/lemon-ui/Tooltip'
import React, { FunctionComponent, ReactElement, useState } from 'react'
import { sceneLogic } from 'scenes/sceneLogic'

import { breadcrumbsLogic } from '~/layout/navigation/Breadcrumbs/breadcrumbsLogic'
import { SidebarChangeNoticeContent, useSidebarChangeNotices } from '~/layout/navigation/SideBar/SidebarChangeNotice'

import { navigation3000Logic } from '../navigationLogic'
import { NavbarItem } from '../types'

export interface NavbarButtonProps extends Pick<LemonButtonProps, 'onClick' | 'icon' | 'sideIcon' | 'to' | 'active'> {
    identifier: string
    icon: ReactElement
    title?: string | ReactElement
    shortTitle?: string
    forceTooltipOnHover?: boolean
    tag?: 'alpha' | 'beta' | 'new'
    sideAction?: NavbarItem['sideAction']
    tooltipDocLink?: string
}

export const NavbarButton: FunctionComponent<NavbarButtonProps> = React.forwardRef<
    HTMLButtonElement,
    NavbarButtonProps
>(
    (
        { identifier, shortTitle, title, forceTooltipOnHover, tag, onClick, sideAction, tooltipDocLink, ...rest },
        ref
    ): JSX.Element => {
        const { activeScene } = useValues(sceneLogic)
        const { sceneBreadcrumbKeys } = useValues(breadcrumbsLogic)
        const { hideNavOnMobile } = useActions(navigation3000Logic)
        const { isNavCollapsed } = useValues(navigation3000Logic)

        const [hasBeenClicked, setHasBeenClicked] = useState(false)

        const here = activeScene === identifier || sceneBreadcrumbKeys.includes(identifier)
        const isNavCollapsedActually = isNavCollapsed

        const buttonProps: LemonButtonProps = { ...rest, active: here }
        let content: JSX.Element | string | undefined
        if (!isNavCollapsedActually) {
            content = shortTitle || title
            if (tag) {
                content = (
                    <>
                        <span className="grow">{content}</span>
                        <LemonTag
                            type={tag === 'alpha' ? 'completion' : tag === 'beta' ? 'warning' : 'success'}
                            size="small"
                            className="ml-2"
                        >
                            {tag.toUpperCase()}
                        </LemonTag>
                    </>
                )
            }
            if (sideAction) {
                // @ts-expect-error - in this case we are perfectly okay with assigning a sideAction
                buttonProps.sideAction = {
                    ...sideAction,
                    divider: true,
                    'data-attr': `menu-item-${sideAction.identifier.toLowerCase()}`,
                }
                buttonProps.sideIcon = null
            }
        } else {
            buttonProps.sideIcon = null
        }

        const buttonContent = (
            <LemonButton
                ref={ref}
                data-attr={`menu-item-${identifier.toString().toLowerCase()}`}
                onMouseEnter={() => setHasBeenClicked(false)}
                onClick={(e) => {
                    if (buttonProps.to) {
                        hideNavOnMobile()
                    }
                    setHasBeenClicked(true)
                    onClick?.(e)
                }}
                className="NavbarButton"
                fullWidth
                type="secondary"
                status="alt"
                {...buttonProps}
            >
                {content}
            </LemonButton>
        )

        const [notices, onAcknowledged] = useSidebarChangeNotices({ identifier })

        return (
            <li className="w-full">
                {notices.length ? (
                    <Tooltip
                        title={<SidebarChangeNoticeContent notices={notices} onAcknowledged={onAcknowledged} />}
                        placement={notices[0].placement ?? 'right'}
                        delayMs={0}
                        visible={true}
                    >
                        {buttonContent}
                    </Tooltip>
                ) : (
                    <Tooltip
                        title={
                            forceTooltipOnHover || isNavCollapsedActually
                                ? here
                                    ? `${title} (you are here)`
                                    : title
                                : null
                        }
                        placement="right"
                        delayMs={forceTooltipOnHover || isNavCollapsedActually ? 0 : undefined}
                        visible={hasBeenClicked ? false : undefined} // Force-hide tooltip after button click
                        docLink={tooltipDocLink}
                    >
                        {buttonContent}
                    </Tooltip>
                )}
            </li>
        )
    }
)
NavbarButton.displayName = 'NavbarButton'
