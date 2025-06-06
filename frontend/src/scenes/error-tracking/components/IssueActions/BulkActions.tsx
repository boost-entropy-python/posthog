import { LemonButton, LemonDialog } from '@posthog/lemon-ui'
import { useActions, useValues } from 'kea'

import { ErrorTrackingIssue } from '~/queries/schema/schema-general'
import { FilterLogicalOperator, HogQLPropertyFilter, PropertyFilterType, UniversalFiltersGroup } from '~/types'

import { errorTrackingSceneLogic } from '../../errorTrackingSceneLogic'
import { AssigneeLabelDisplay } from '../Assignee/AssigneeDisplay'
import { AssigneeSelect } from '../Assignee/AssigneeSelect'
import { errorFiltersLogic } from '../ErrorFilters/errorFiltersLogic'
import { GenericSelect } from '../GenericSelect'
import { IssueStatus, StatusIndicator } from '../Indicator'
import { issueActionsLogic } from './issueActionsLogic'

export interface BulkActionsProps {
    issues: ErrorTrackingIssue[]
    selectedIds: string[]
}

export function BulkActions({ issues, selectedIds }: BulkActionsProps): JSX.Element {
    const { mergeIssues, assignIssues, resolveIssues, suppressIssues, activateIssues } = useActions(issueActionsLogic)
    const { filterGroup } = useValues(errorFiltersLogic)
    const { setFilterGroup } = useActions(errorFiltersLogic)
    const { setSelectedIssueIds } = useActions(errorTrackingSceneLogic)

    const hasAtLeastTwoIssues = selectedIds.length >= 2

    const excludeSelectedIssues = (): void => {
        const quotedIds = selectedIds.map((id) => `'${id}'`).join(', ')
        const newFilter: HogQLPropertyFilter = {
            key: `issue_id NOT IN (${quotedIds})`,
            type: PropertyFilterType.HogQL,
            value: null,
        }

        const firstGroup = filterGroup.values[0] as UniversalFiltersGroup

        const updatedFirstGroup = { ...firstGroup, values: [...firstGroup.values, newFilter] }

        setFilterGroup({
            type: FilterLogicalOperator.And,
            values: [updatedFirstGroup],
        })
        setSelectedIssueIds([])
    }

    const currentStatus = issues
        .filter((issue: ErrorTrackingIssue) => selectedIds.includes(issue.id))
        .map((issue: ErrorTrackingIssue) => issue.status as IssueStatus)
        .reduce<IssueStatus | 'mixed' | null>((acc, status) => {
            if (acc === null) {
                return status
            } else if (acc === 'mixed') {
                return 'mixed'
            } else if (acc !== status) {
                return 'mixed'
            }
            return acc
        }, null)

    return (
        <div className="flex gap-x-2 justify-between">
            <div className="flex gap-x-2">
                <LemonButton
                    disabledReason={!hasAtLeastTwoIssues ? 'Select at least two issues to merge' : null}
                    type="secondary"
                    size="small"
                    onClick={() =>
                        LemonDialog.open({
                            title: 'Merge Issues',
                            content: `Are you sure you want to merge these ${selectedIds.length} issues?`,
                            primaryButton: {
                                children: 'Merge',
                                status: 'danger',
                                onClick: () => {
                                    mergeIssues(selectedIds)
                                },
                            },
                        })
                    }
                >
                    Merge
                </LemonButton>
                <GenericSelect
                    size="small"
                    current={currentStatus == 'mixed' ? null : currentStatus}
                    values={['active', 'resolved', 'suppressed']}
                    placeholder="Mark as"
                    renderValue={(value) => {
                        return (
                            <StatusIndicator
                                status={value as IssueStatus}
                                size="small"
                                className="w-full"
                                withTooltip={true}
                            />
                        )
                    }}
                    onChange={(value) => {
                        if (value == currentStatus) {
                            return
                        }
                        switch (value) {
                            case 'resolved':
                                resolveIssues(selectedIds)
                                break
                            case 'suppressed':
                                suppressIssues(selectedIds)
                                break
                            case 'active':
                                activateIssues(selectedIds)
                                break
                            default:
                                break
                        }
                    }}
                />
                <AssigneeSelect assignee={null} onChange={(assignee) => assignIssues(selectedIds, assignee)}>
                    {(displayAssignee) => (
                        <LemonButton type="secondary" size="small">
                            <AssigneeLabelDisplay assignee={displayAssignee} placeholder="Assign" />
                        </LemonButton>
                    )}
                </AssigneeSelect>
            </div>
            <LemonButton type="secondary" size="small" onClick={excludeSelectedIssues}>
                Hide from search
            </LemonButton>
        </div>
    )
}
