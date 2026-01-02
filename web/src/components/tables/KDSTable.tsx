/**
 * KDS Table Component
 *
 * Feature-rich table with KDS styling, sorting, filtering, and export.
 * Uses TanStack Table (React Table v8) for core functionality.
 */

import React, { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  ColumnDef,
  flexRender,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { useTheme } from '../../contexts/ThemeContext';

interface TableConfig {
  title?: string;
  description?: string;
  columns: any[];
  data: any[];
  pagination?: {
    enabled: boolean;
    page_size: number;
    page_size_options: number[];
  };
  style?: {
    striped_rows?: boolean;
    hover_highlight?: boolean;
    bordered?: boolean;
    compact?: boolean;
    row_height?: number;
  };
  global_search_enabled?: boolean;
  show_totals_row?: boolean;
  export_config?: {
    enabled: boolean;
    formats: string[];
  };
}

interface KDSTableProps {
  config: TableConfig;
  onRowClick?: (row: any) => void;
  onExport?: (format: string) => void;
}

export function KDSTable({ config, onRowClick, onExport }: KDSTableProps) {
  const { colors } = useTheme();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  // Convert config columns to TanStack Table columns
  const columns = useMemo<ColumnDef<any>[]>(() => {
    return config.columns.map((col) => ({
      accessorKey: col.key,
      header: col.header,
      size: col.width || col.min_width || 150,
      enableSorting: col.sortable !== false,
      enableColumnFilter: col.filterable !== false,
      cell: (info) => formatCell(info.getValue(), col),
      footer: col.footer_aggregate
        ? () => calculateAggregate(config.data, col.key, col.footer_aggregate)
        : undefined,
    }));
  }, [config.columns, config.data]);

  // Initialize table
  const table = useReactTable({
    data: config.data,
    columns,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: config.pagination?.enabled
      ? getPaginationRowModel()
      : undefined,
    initialState: {
      pagination: {
        pageSize: config.pagination?.page_size || 25,
      },
    },
  });

  // Styles
  const tableStyle = config.style || {};
  const rowHeight = tableStyle.row_height || 48;

  return (
    <div
      style={{
        backgroundColor: colors.backgroundPrimary,
        borderRadius: '8px',
        border: `1px solid ${colors.borderSecondary}`,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      {(config.title || config.global_search_enabled || config.export_config?.enabled) && (
        <div
          style={{
            padding: '16px',
            borderBottom: `1px solid ${colors.borderSecondary}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          {/* Title */}
          {config.title && (
            <div>
              <h3
                style={{
                  margin: 0,
                  fontSize: '18px',
                  fontWeight: 'bold',
                  color: colors.textPrimary,
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                {config.title}
              </h3>
              {config.description && (
                <p
                  style={{
                    margin: '4px 0 0 0',
                    fontSize: '14px',
                    color: colors.textSecondary,
                  }}
                >
                  {config.description}
                </p>
              )}
            </div>
          )}

          {/* Search and Export */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* Global Search */}
            {config.global_search_enabled && (
              <input
                type="text"
                value={globalFilter}
                onChange={(e) => setGlobalFilter(e.target.value)}
                placeholder="Search..."
                style={{
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: `1px solid ${colors.borderSecondary}`,
                  backgroundColor: colors.backgroundSecondary,
                  color: colors.textPrimary,
                  fontSize: '14px',
                  fontFamily: 'Inter, sans-serif',
                  outline: 'none',
                  width: '200px',
                }}
              />
            )}

            {/* Export Buttons */}
            {config.export_config?.enabled &&
              config.export_config.formats.map((format) => (
                <button
                  key={format}
                  onClick={() => onExport?.(format)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: `1px solid ${colors.borderPrimary}`,
                    backgroundColor: colors.backgroundSecondary,
                    color: colors.brandPrimary,
                    fontSize: '14px',
                    fontWeight: 500,
                    cursor: 'pointer',
                    fontFamily: 'Inter, sans-serif',
                  }}
                >
                  Export {format.toUpperCase()}
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontFamily: 'Inter, sans-serif',
          }}
        >
          {/* Header */}
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{
                      padding: '12px 16px',
                      textAlign: 'left',
                      fontWeight: 600,
                      fontSize: '14px',
                      color: colors.textPrimary,
                      backgroundColor: colors.backgroundSecondary,
                      borderBottom: `2px solid ${colors.borderPrimary}`,
                      cursor: header.column.getCanSort() ? 'pointer' : 'default',
                      userSelect: 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {/* Sort indicator */}
                      {header.column.getCanSort() && (
                        <span style={{ fontSize: '12px' }}>
                          {{
                            asc: '↑',
                            desc: '↓',
                          }[header.column.getIsSorted() as string] ?? '⇅'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>

          {/* Body */}
          <tbody>
            {table.getRowModel().rows.map((row, idx) => (
              <tr
                key={row.id}
                onClick={() => onRowClick?.(row.original)}
                style={{
                  backgroundColor:
                    tableStyle.striped_rows && idx % 2 === 1
                      ? colors.backgroundSecondary
                      : colors.backgroundPrimary,
                  cursor: onRowClick ? 'pointer' : 'default',
                  transition: 'background-color 0.15s',
                }}
                onMouseEnter={(e) => {
                  if (tableStyle.hover_highlight) {
                    e.currentTarget.style.backgroundColor = colors.backgroundTertiary;
                  }
                }}
                onMouseLeave={(e) => {
                  if (tableStyle.hover_highlight) {
                    e.currentTarget.style.backgroundColor =
                      tableStyle.striped_rows && idx % 2 === 1
                        ? colors.backgroundSecondary
                        : colors.backgroundPrimary;
                  }
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    style={{
                      padding: '12px 16px',
                      fontSize: '14px',
                      color: colors.textPrimary,
                      borderBottom: tableStyle.bordered
                        ? `1px solid ${colors.borderSecondary}`
                        : 'none',
                      height: `${rowHeight}px`,
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>

          {/* Footer (Totals) */}
          {config.show_totals_row && (
            <tfoot>
              {table.getFooterGroups().map((footerGroup) => (
                <tr key={footerGroup.id}>
                  {footerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontWeight: 600,
                        fontSize: '14px',
                        color: colors.textPrimary,
                        backgroundColor: colors.backgroundSecondary,
                        borderTop: `2px solid ${colors.borderPrimary}`,
                      }}
                    >
                      {flexRender(header.column.columnDef.footer, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </tfoot>
          )}
        </table>
      </div>

      {/* Pagination */}
      {config.pagination?.enabled && (
        <div
          style={{
            padding: '16px',
            borderTop: `1px solid ${colors.borderSecondary}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          {/* Page info */}
          <div style={{ fontSize: '14px', color: colors.textSecondary }}>
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              table.getFilteredRowModel().rows.length
            )}{' '}
            of {table.getFilteredRowModel().rows.length} rows
          </div>

          {/* Page controls */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: `1px solid ${colors.borderSecondary}`,
                backgroundColor: colors.backgroundSecondary,
                color: colors.textPrimary,
                fontSize: '14px',
                cursor: table.getCanPreviousPage() ? 'pointer' : 'not-allowed',
                opacity: table.getCanPreviousPage() ? 1 : 0.5,
              }}
            >
              Previous
            </button>

            <span style={{ fontSize: '14px', color: colors.textSecondary }}>
              Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
            </span>

            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: `1px solid ${colors.borderSecondary}`,
                backgroundColor: colors.backgroundSecondary,
                color: colors.textPrimary,
                fontSize: '14px',
                cursor: table.getCanNextPage() ? 'pointer' : 'not-allowed',
                opacity: table.getCanNextPage() ? 1 : 0.5,
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Format cell value based on column configuration
 */
function formatCell(value: any, column: any): React.ReactNode {
  if (value === null || value === undefined) {
    return <span style={{ color: '#888' }}>—</span>;
  }

  switch (column.type) {
    case 'currency':
      return formatCurrency(value, column.currency_format);
    case 'percentage':
      return formatPercentage(value, column.percentage_format);
    case 'number':
      return formatNumber(value, column.number_format);
    case 'date':
    case 'datetime':
      return formatDate(value, column.date_format);
    case 'boolean':
      return value ? '✓' : '✗';
    default:
      return value;
  }
}

function formatCurrency(value: number, format?: any): string {
  const fmt = format || {};
  const symbol = fmt.symbol || '$';
  const decimals = fmt.decimals ?? 0;
  const abbreviate = fmt.abbreviate || false;

  let formatted = Math.abs(value);

  if (abbreviate && formatted >= 1000000) {
    if (formatted >= 1000000000) {
      formatted = formatted / 1000000000;
      return `${symbol}${formatted.toFixed(decimals)}B`;
    } else {
      formatted = formatted / 1000000;
      return `${symbol}${formatted.toFixed(decimals)}M`;
    }
  } else if (abbreviate && formatted >= 1000) {
    formatted = formatted / 1000;
    return `${symbol}${formatted.toFixed(decimals)}K`;
  }

  return `${symbol}${formatted.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
}

function formatPercentage(value: number, format?: any): string {
  const fmt = format || {};
  const decimals = fmt.decimals ?? 1;
  const multiply = fmt.multiply_by_100 ?? true;

  const pctValue = multiply ? value * 100 : value;
  return `${pctValue.toFixed(decimals)}%`;
}

function formatNumber(value: number, format?: any): string {
  const fmt = format || {};
  const decimals = fmt.decimals ?? 0;
  const abbreviate = fmt.abbreviate || false;

  let formatted = Math.abs(value);

  if (abbreviate && formatted >= 1000000) {
    if (formatted >= 1000000000) {
      formatted = formatted / 1000000000;
      return `${formatted.toFixed(decimals)}B`;
    } else {
      formatted = formatted / 1000000;
      return `${formatted.toFixed(decimals)}M`;
    }
  } else if (abbreviate && formatted >= 1000) {
    formatted = formatted / 1000;
    return `${formatted.toFixed(decimals)}K`;
  }

  return formatted.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatDate(value: any, format?: any): string {
  const date = new Date(value);
  return date.toLocaleDateString();
}

function calculateAggregate(data: any[], key: string, type: string): string {
  const values = data.map((row) => row[key]).filter((v) => v != null);

  if (values.length === 0) return '—';

  switch (type) {
    case 'sum':
      return values.reduce((a, b) => a + b, 0).toLocaleString();
    case 'avg':
      return (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);
    case 'min':
      return Math.min(...values).toLocaleString();
    case 'max':
      return Math.max(...values).toLocaleString();
    case 'count':
      return values.length.toString();
    default:
      return '—';
  }
}

export default KDSTable;
