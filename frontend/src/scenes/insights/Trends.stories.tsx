import { Meta, StoryObj } from '@storybook/react'
import { App } from 'scenes/App'
import { createInsightStory } from 'scenes/insights/__mocks__/createInsightScene'
import { samplePersonProperties, sampleRetentionPeopleResponse } from 'scenes/insights/__mocks__/insight.mocks'

import { mswDecorator } from '~/mocks/browser'

type Story = StoryObj<typeof App>
const meta: Meta = {
    title: 'Scenes-App/Insights/Trends',
    parameters: {
        layout: 'fullscreen',
        testOptions: {
            snapshotBrowsers: ['chromium'],
            viewport: {
                // needs a slightly larger width to push the rendered scene away from breakpoint boundary
                width: 1300,
                height: 720,
            },
        },
        viewMode: 'story',
        mockDate: '2022-03-11',
    },
    decorators: [
        mswDecorator({
            get: {
                '/api/environments/:team_id/persons/retention': sampleRetentionPeopleResponse,
                '/api/environments/:team_id/persons/properties': samplePersonProperties,
                '/api/projects/:team_id/groups_types': [],
            },
            post: {
                '/api/projects/:team_id/cohorts/': { id: 1 },
            },
        }),
    ],
}
export default meta
/* eslint-disable @typescript-eslint/no-var-requires */
// Trends
export const TrendsLine: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsLine.json')
)
TrendsLine.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsLineEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsLine.json'),
    'edit'
)
TrendsLineEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsLineMulti: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsLineMulti.json')
)
TrendsLineMulti.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}
export const TrendsLineMultiEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsLineMulti.json'),
    'edit'
)
TrendsLineMultiEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsLineBreakdown: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsLineBreakdown.json')
)
TrendsLineBreakdown.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}
export const TrendsLineBreakdownEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsLineBreakdown.json'),
    'edit'
)
TrendsLineBreakdownEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsLineBreakdownLabels: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsLineBreakdown.json'),
    'view',
    true
)
TrendsLineBreakdownLabels.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsBar: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsBar.json')
)
TrendsBar.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}
export const TrendsBarEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsBar.json'),
    'edit'
)
TrendsBarEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsBarBreakdown: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsBarBreakdown.json')
)
TrendsBarBreakdown.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}
export const TrendsBarBreakdownEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsBarBreakdown.json'),
    'edit'
)
TrendsBarBreakdownEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsValue: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsValue.json')
)
TrendsValue.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-bar-value-graph] > canvas' },
}
export const TrendsValueEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsValue.json'),
    'edit'
)
TrendsValueEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-bar-value-graph] > canvas' },
}

export const TrendsValueBreakdown: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsValueBreakdown.json')
)
TrendsValueBreakdown.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-bar-value-graph] > canvas' },
}
export const TrendsValueBreakdownEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsValueBreakdown.json'),
    'edit'
)
TrendsValueBreakdownEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-bar-value-graph] > canvas' },
}

export const TrendsArea: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsArea.json')
)
TrendsArea.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}
export const TrendsAreaEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsArea.json'),
    'edit'
)
TrendsAreaEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsAreaBreakdown: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsAreaBreakdown.json')
)
TrendsAreaBreakdown.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}
export const TrendsAreaBreakdownEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsAreaBreakdown.json'),
    'edit'
)
TrendsAreaBreakdownEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
}

export const TrendsNumber: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsNumber.json')
)
TrendsNumber.parameters = { testOptions: { waitForSelector: '.BoldNumber__value' } }
export const TrendsNumberEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsNumber.json'),
    'edit'
)
TrendsNumberEdit.parameters = { testOptions: { waitForSelector: '.BoldNumber__value' } }

export const TrendsTable: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsTable.json')
)
TrendsTable.parameters = { testOptions: { waitForSelector: '[data-attr=insights-table-graph] td' } }
export const TrendsTableEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsTable.json'),
    'edit'
)
TrendsTableEdit.parameters = { testOptions: { waitForSelector: '[data-attr=insights-table-graph] td' } }

export const TrendsTableBreakdown: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsTableBreakdown.json')
)
TrendsTableBreakdown.parameters = { testOptions: { waitForSelector: '[data-attr=insights-table-graph] td' } }
export const TrendsTableBreakdownEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsTableBreakdown.json'),
    'edit'
)
TrendsTableBreakdownEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=insights-table-graph] td' },
}

export const TrendsPie: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsPie.json')
)
TrendsPie.parameters = { testOptions: { waitForSelector: '[data-attr=trend-pie-graph] > canvas' } }
export const TrendsPieEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsPie.json'),
    'edit'
)
TrendsPieEdit.parameters = { testOptions: { waitForSelector: '[data-attr=trend-pie-graph] > canvas' } }

export const TrendsPieBreakdown: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsPieBreakdown.json')
)
TrendsPieBreakdown.parameters = { testOptions: { waitForSelector: '[data-attr=trend-pie-graph] > canvas' } }
export const TrendsPieBreakdownEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsPieBreakdown.json'),
    'edit'
)
TrendsPieBreakdownEdit.parameters = {
    testOptions: { waitForSelector: '[data-attr=trend-pie-graph] > canvas' },
}

export const TrendsPieBreakdownLabels: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsPieBreakdown.json'),
    'view',
    true
)
TrendsPieBreakdownLabels.parameters = { testOptions: { waitForSelector: '[data-attr=trend-pie-graph] > canvas' } }

export const TrendsWorldMap: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsWorldMap.json')
)
TrendsWorldMap.parameters = { testOptions: { waitForSelector: '.WorldMap' } }
export const TrendsWorldMapEdit: Story = createInsightStory(
    require('../../mocks/fixtures/api/projects/team_id/insights/trendsWorldMap.json'),
    'edit'
)
TrendsWorldMapEdit.parameters = { testOptions: { waitForSelector: '.WorldMap' } }

// Stickiness
// export const Stickiness: Story = createInsightStory(
//     require('../../mocks/fixtures/api/projects/team_id/insights/stickiness.json')
// )
// Stickiness.parameters = {
//     testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
// }
// export const StickinessEdit: Story = createInsightStory(
//     require('../../mocks/fixtures/api/projects/team_id/insights/stickiness.json'),
//     'edit'
// )
// StickinessEdit.parameters = {
//     testOptions: { waitForSelector: '[data-attr=trend-line-graph] > canvas' },
// }
/* eslint-enable @typescript-eslint/no-var-requires */
